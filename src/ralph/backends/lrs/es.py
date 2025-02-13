"""Elasticsearch LRS backend for Ralph."""

import logging
from collections.abc import Iterator, Mapping, Sequence

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.es import (
    ESDataBackend,
    ESDataBackendSettings,
    ESQuery,
    ESQueryPit,
)
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
    ids_adapter,
    include_extra_adapter,
    params_adapter,
    target_adapter,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class ESLRSBackendSettings(BaseLRSBackendSettings, ESDataBackendSettings):
    """Elasticsearch LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__ES__"),
    }


class ESLRSBackend(BaseLRSBackend[ESLRSBackendSettings], ESDataBackend):
    """Elasticsearch LRS backend implementation."""

    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        query = self.get_query(params=params)
        try:
            es_documents = self.read(
                query=query, target=target, chunk_size=params.limit
            )
            statements = [document["_source"]["statement"] for document in es_documents]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        query = self.query_class(query={"terms": {"_id": ids}})

        try:
            es_response = self.read(query=query, target=target)

            for document in es_response:
                if include_extra:
                    yield document["_source"]
                else:
                    yield document["_source"]["statement"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> ESQuery:
        """Construct query from statement parameters."""
        es_query_filters = []

        if params.statement_id:
            es_query_filters += [
                {"term": {"_id": params.statement_id}},
                {"term": {"metadata.voided": False}},
            ]

        elif params.voided_statement_id:
            es_query_filters += [
                {"term": {"_id": params.voided_statement_id}},
                {"term": {"metadata.voided": True}},
            ]

        ESLRSBackend._add_agent_filters(es_query_filters, params.agent, "actor")
        ESLRSBackend._add_agent_filters(es_query_filters, params.authority, "authority")

        if params.verb:
            es_query_filters += [{"term": {"statement.verb.id.keyword": params.verb}}]

        if params.activity:
            es_query_filters += [
                {"term": {"statement.object.id.keyword": params.activity}},
            ]

        if params.since:
            es_query_filters += [
                {"range": {"statement.timestamp": {"gt": params.since}}}
            ]

        if params.until:
            es_query_filters += [
                {"range": {"statement.timestamp": {"lte": params.until}}}
            ]

        es_query = {
            "pit": ESQueryPit.model_construct(id=params.pit_id),
            "size": params.limit,
            "sort": [
                {
                    "statement.timestamp": {
                        "order": "asc" if params.ascending else "desc"
                    }
                }
            ],
        }
        if len(es_query_filters) > 0:
            es_query["query"] = {"bool": {"filter": es_query_filters}}

        if params.ignore_order:
            es_query["sort"] = "_shard_doc"

        if params.search_after:
            es_query["search_after"] = params.search_after.split("|")

        # Note: `params` fields are validated thus we skip their validation in ESQuery.
        return ESQuery.model_construct(**es_query)

    @staticmethod
    def _add_agent_filters(
        es_query_filters: Sequence,
        agent_params: AgentParameters | Mapping,
        target_field: str,
    ) -> None:
        """Add filters relative to agents to `es_query_filters`."""
        if not agent_params:
            return

        if not isinstance(agent_params, Mapping):
            agent_params = agent_params.model_dump()

        if agent_params.get("mbox"):
            field = f"statement.{target_field}.mbox.keyword"
            es_query_filters += [{"term": {field: agent_params.get("mbox")}}]

        elif agent_params.get("mbox_sha1sum"):
            field = f"statement.{target_field}.mbox_sha1sum.keyword"
            es_query_filters += [{"term": {field: agent_params.get("mbox_sha1sum")}}]

        elif agent_params.get("openid"):
            field = f"statement.{target_field}.openid.keyword"
            es_query_filters += [{"term": {field: agent_params.get("openid")}}]

        elif agent_params.get("account__name"):
            field = f"statement.{target_field}.account.name.keyword"
            es_query_filters += [{"term": {field: agent_params.get("account__name")}}]

            field = f"statement.{target_field}.account.homePage.keyword"
            es_query_filters += [
                {"term": {field: agent_params.get("account__home_page")}}
            ]

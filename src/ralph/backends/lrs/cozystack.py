"""CozyStack LRS backend for Ralph."""

import logging
from collections.abc import Iterator, Mapping, Sequence
from enum import StrEnum

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.cozystack import (
    CozyStackDataBackend,
    CozyStackDataBackendSettings,
    CozyStackQuery,
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


class SortDirectionEnum(StrEnum):
    """CozyStack sort direction enum."""

    ASC = "asc"
    DESC = "desc"


class CozyStackLRSBackendSettings(BaseLRSBackendSettings, CozyStackDataBackendSettings):
    """CozyStack LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__COZYSTACK__"),
    }


class CozyStackLRSBackend(
    BaseLRSBackend[CozyStackLRSBackendSettings], CozyStackDataBackend
):
    """CozyStack LRS backend."""

    @staticmethod
    def _add_agent_filters(
        query_filters: Mapping,
        agent_params: AgentParameters,
        target_field: str,
    ) -> None:
        """Add filters relative to agents to cozystack_query_filters.

        Args:
            query_filters (dict): Filters passed to CozyStack query.
            agent_params (AgentParameters): Agent query parameters to search for.
            target_field (str): The target agent field name to perform the search.
        """
        if not agent_params:
            return

        prefix = f"source.statement.{target_field}"

        for agent_field in ["mbox", "mbox_sha1sum", "openid"]:
            if agent_params.get(agent_field):
                query_filters[f"{prefix}.{agent_field}"] = agent_params[agent_field]

        if agent_params.get("account__name"):
            query_filters[f"{prefix}.account.name"] = agent_params.get("account__name")
            query_filters[f"{prefix}.account.homePage"] = agent_params.get(
                "account__home_page"
            )

    @staticmethod
    def _get_query(params: RalphStatementsQuery) -> CozyStackQuery:
        """Construct query from statement parameters."""
        cozystack_query_filters = {}

        if params.statement_id:
            cozystack_query_filters["source.statement.id"] = params.statement_id
            cozystack_query_filters["source.metadata.voided"] = False

        elif params.voided_statement_id:
            cozystack_query_filters["source.statement.id"] = params.voided_statement_id
            cozystack_query_filters["source.metadata.voided"] = True

        CozyStackLRSBackend._add_agent_filters(
            cozystack_query_filters, params.agent, "actor"
        )

        CozyStackLRSBackend._add_agent_filters(
            cozystack_query_filters, params.authority, "authority"
        )

        if params.verb:
            cozystack_query_filters["source.statement.verb.id"] = params.verb

        if params.activity:
            cozystack_query_filters["source.statement.object.id"] = params.activity

        if params.since:
            cozystack_query_filters["source.statement.timestamp"] = {
                "$gt": params.since
            }

        if params.until:
            if "source.statement.timestamp" not in cozystack_query_filters:
                cozystack_query_filters["source.statement.timestamp"] = {}

            cozystack_query_filters["source.statement.timestamp"]["$lte"] = params.until

        cozystack_sort_order = (
            SortDirectionEnum.ASC if params.ascending else SortDirectionEnum.DESC
        )

        cozystack_query_sort = [
            {"source.statement.timestamp": cozystack_sort_order},
            {"source.statement.id": cozystack_sort_order},
        ]

        # Note: `params` fields are validated thus we skip CozyStackQuery validation.
        return CozyStackQuery.model_construct(
            selector=cozystack_query_filters,
            limit=params.limit,
            sort=cozystack_query_sort,
            bookmark=params.search_after if params.search_after else None,
            fields=["_id", "source"],
        )

    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the results of a statements query using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        query = self._get_query(params)

        try:
            response = list(
                self.read(query=query, target=target, chunk_size=params.limit)
            )

        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CozyStack")
            raise error

        search_after = query.bookmark if query.next else None

        return StatementQueryResult(
            statements=[document["source"]["statement"] for document in response],
            search_after=search_after,
        )

    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        query = self.query_class(selector={"source.statement.id": {"$in": ids}})

        try:
            response = self.read(query=query, target=target)

            for document in response:
                if include_extra:
                    yield {
                        "statement": {
                            **document["source"]["statement"],
                            "_rev": document.pop("_rev"),
                        },
                        "metadata": document["source"]["metadata"],
                    }
                else:
                    yield document["source"]["statement"]

        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CozyStack")
            raise error

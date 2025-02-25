"""MongoDB LRS backend for Ralph."""

import logging
from collections.abc import Iterator, Mapping, Sequence

from bson.objectid import ObjectId
from pydantic_settings import SettingsConfigDict
from pymongo import ASCENDING, DESCENDING

from ralph.backends.data.mongo import (
    MongoDataBackend,
    MongoDataBackendSettings,
    MongoQuery,
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


class MongoLRSBackendSettings(BaseLRSBackendSettings, MongoDataBackendSettings):
    """MongoDB LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__MONGO__"),
    }


class MongoLRSBackend(BaseLRSBackend[MongoLRSBackendSettings], MongoDataBackend):
    """MongoDB LRS backend."""

    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the results of a statements query using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        query = self.get_query(params)
        try:
            mongo_response = list(
                self.read(query=query, target=target, chunk_size=params.limit)
            )
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error

        search_after = None
        if mongo_response:
            search_after = mongo_response[-1]["_id"]

        return StatementQueryResult(
            statements=[
                document["_source"]["statement"] for document in mongo_response
            ],
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        query = self.query_class(filter={"_source.statement.id": {"$in": ids}})
        try:
            mongo_response = self.read(query=query, target=target)

            for document in mongo_response:
                if include_extra:
                    yield document["_source"]
                else:
                    yield document["_source"]["statement"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> MongoQuery:
        """Construct query from statement parameters."""
        mongo_query_filters = {}

        if params.statement_id:
            mongo_query_filters.update(
                {
                    "_source.statement.id": params.statement_id,
                    "_source.metadata.voided": False,
                },
            )

        elif params.voided_statement_id:
            mongo_query_filters.update(
                {
                    "_source.statement.id": params.voided_statement_id,
                    "_source.metadata.voided": True,
                },
            )
        else:
            mongo_query_filters.update(
                {
                    "_source.metadata.voided": False,
                },
            )

        MongoLRSBackend._add_agent_filters(mongo_query_filters, params.agent, "actor")
        MongoLRSBackend._add_agent_filters(
            mongo_query_filters, params.authority, "authority"
        )

        if params.verb:
            mongo_query_filters.update({"_source.statement.verb.id": params.verb})

        if params.activity:
            mongo_query_filters.update(
                {
                    "_source.statement.object.id": params.activity,
                },
            )

        if params.since:
            mongo_query_filters.update(
                {"_source.statement.timestamp": {"$gt": params.since}}
            )

        if params.until:
            if not params.since:
                mongo_query_filters["_source.statement.timestamp"] = {}
            mongo_query_filters["_source.statement.timestamp"].update(
                {"$lte": params.until}
            )

        if params.search_after:
            search_order = "$gt" if params.ascending else "$lt"
            mongo_query_filters.update(
                {"_id": {search_order: ObjectId(params.search_after)}}
            )

        mongo_sort_order = ASCENDING if params.ascending else DESCENDING
        mongo_query_sort = [
            ("_source.statement.timestamp", mongo_sort_order),
            ("_id", mongo_sort_order),
        ]

        # Note: `params` fields are validated thus we skip MongoQuery validation.
        return MongoQuery.model_construct(
            filter=mongo_query_filters, limit=params.limit, sort=mongo_query_sort
        )

    @staticmethod
    def _add_agent_filters(
        mongo_query_filters: Mapping,
        agent_params: AgentParameters | Mapping,
        target_field: str,
    ) -> None:
        """Add filters relative to agents to mongo_query_filters.

        Args:
            mongo_query_filters (dict): Filters passed to MongoDB query.
            agent_params (AgentParameters): Agent query parameters to search for.
            target_field (str): The target agent field name to perform the search.
        """
        if not agent_params:
            return

        if not isinstance(agent_params, Mapping):
            agent_params = agent_params.model_dump()

        if agent_params.get("mbox"):
            key = f"_source.statement.{target_field}.mbox"
            mongo_query_filters.update({key: agent_params.get("mbox")})

        if agent_params.get("mbox_sha1sum"):
            key = f"_source.statement.{target_field}.mbox_sha1sum"
            mongo_query_filters.update({key: agent_params.get("mbox_sha1sum")})

        if agent_params.get("openid"):
            key = f"_source.statement.{target_field}.openid"
            mongo_query_filters.update({key: agent_params.get("openid")})

        if agent_params.get("account__name"):
            key = f"_source.statement.{target_field}.account.name"
            mongo_query_filters.update({key: agent_params.get("account__name")})
            key = f"_source.statement.{target_field}.account.homePage"
            mongo_query_filters.update({key: agent_params.get("account__home_page")})

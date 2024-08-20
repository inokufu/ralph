"""CouchDB LRS backend for Ralph."""

import logging
from typing import Iterator, List, Optional

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.couch import (
    CouchDataBackend,
    CouchDataBackendSettings,
    CouchQuery,
)
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)

from enum import StrEnum
class SortDirectionEnum(StrEnum):
    ASC = "asc"
    DESC = "desc"


class CouchLRSBackendSettings(BaseLRSBackendSettings, CouchDataBackendSettings):
    """CouchDB LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__COUCH__"),
    }


class CouchLRSBackend(BaseLRSBackend[CouchLRSBackendSettings], CouchDataBackend):
    """CouchDB LRS backend."""

    def query_statements(
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the results of a statements query using xAPI parameters."""
        query = self.get_query(params)
        try:
            couch_response = list(
                self.read(query=query, target=target, chunk_size=params.limit)
            )
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CouchDB")
            raise error

        search_after = None
        if couch_response:
            search_after = couch_response[-1]["bookmark"]

        return StatementQueryResult(
            statements=[document["source"] for document in couch_response],
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        query = self.query_class(selector={"source.id": {"$in": ids}})
        try:
            couch_response = self.read(query=query, target=target)
            yield from (document["source"] for document in couch_response)
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CouchDB")
            raise error

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> CouchQuery:
        """Construct query from statement parameters."""
        couch_query_filters = {}

        if params.statement_id:
            couch_query_filters.update({"source.id": params.statement_id})

        CouchLRSBackend._add_agent_filters(couch_query_filters, params.agent, "actor")
        CouchLRSBackend._add_agent_filters(
            couch_query_filters, params.authority, "authority"
        )

        if params.verb:
            couch_query_filters.update({"source.verb.id": params.verb})

        if params.activity:
            couch_query_filters.update(
                {
                    "source.object.id": params.activity,
                },
            )

        if params.since:
            couch_query_filters.update({"source.timestamp": {"$gt": params.since}})

        if params.until:
            if not params.since:
                couch_query_filters["source.timestamp"] = {}
            couch_query_filters["source.timestamp"].update({"$lte": params.until})

        couch_sort_order = SortDirectionEnum.ASC if params.ascending else SortDirectionEnum.DESC
        couch_query_sort = [
            {"source.timestamp": couch_sort_order},
            {"_id": couch_sort_order},
        ]

        # Note: `params` fields are validated thus we skip CouchQuery validation.
        return CouchQuery.model_construct(
            filter=couch_query_filters, limit=params.limit, sort=couch_query_sort,
            bookmark=params.search_after if params.search_after else None,
            # TODO: We might need to make the field parameter more dynamical --> Not sure about that
            fields=["_id", "source"]
        )

    @staticmethod
    def _add_agent_filters(
        couch_query_filters: dict, agent_params: AgentParameters, target_field: str
    ) -> None:
        """Add filters relative to agents to couch_query_filters.

        Args:
            couch_query_filters (dict): Filters passed to CouchDB query.
            agent_params (AgentParameters): Agent query parameters to search for.
            target_field (str): The target agent field name to perform the search.
        """
        if not agent_params:
            return

        if not isinstance(agent_params, dict):
            agent_params = agent_params.model_dump()

        if agent_params.get("mbox"):
            key = f"source.{target_field}.mbox"
            couch_query_filters.update({key: agent_params.get("mbox")})

        if agent_params.get("mbox_sha1sum"):
            key = f"source.{target_field}.mbox_sha1sum"
            couch_query_filters.update({key: agent_params.get("mbox_sha1sum")})

        if agent_params.get("openid"):
            key = f"source.{target_field}.openid"
            couch_query_filters.update({key: agent_params.get("openid")})

        if agent_params.get("account__name"):
            key = f"source.{target_field}.account.name"
            couch_query_filters.update({key: agent_params.get("account__name")})
            key = f"source.{target_field}.account.homePage"
            couch_query_filters.update({key: agent_params.get("account__home_page")})

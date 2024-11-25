"""CozyStack LRS backend for Ralph."""

import logging
from enum import StrEnum
from typing import Iterator, List, Optional

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
        query_filters: dict, agent_params: AgentParameters, target_field: str
    ) -> None:
        """Add filters relative to agents to cozystack_query_filters.

        Args:
            query_filters (dict): Filters passed to CozyStack query.
            agent_params (AgentParameters): Agent query parameters to search for.
            target_field (str): The target agent field name to perform the search.
        """
        if not agent_params:
            return

        if not isinstance(agent_params, dict):
            agent_params = agent_params.model_dump()

        prefix = f"source.{target_field}"

        if agent_params.get("mbox"):
            query_filters[f"{prefix}.mbox"] = agent_params["mbox"]

        if agent_params.get("mbox_sha1sum"):
            query_filters[f"{prefix}.mbox_sha1sum"] = agent_params["mbox_sha1sum"]

        if agent_params.get("openid"):
            query_filters[f"{prefix}.openid"] = agent_params["openid"]

        if agent_params.get("account__name"):
            query_filters[f"{prefix}.account.name"] = agent_params.get("account__name")
            query_filters[f"{prefix}.account.homePage"] = agent_params.get(
                "account__home_page"
            )

    @staticmethod
    def get_query(params: RalphStatementsQuery) -> CozyStackQuery:
        """Construct query from statement parameters."""
        cozystack_query_filters = {}

        if params.statement_id:
            cozystack_query_filters["source.id"] = params.statement_id

        CozyStackLRSBackend._add_agent_filters(
            cozystack_query_filters, params.agent, "actor"
        )

        CozyStackLRSBackend._add_agent_filters(
            cozystack_query_filters, params.authority, "authority"
        )

        if params.verb:
            cozystack_query_filters["source.verb.id"] = params.verb

        if params.activity:
            cozystack_query_filters["source.object.id"] = params.activity

        if params.since:
            cozystack_query_filters["source.timestamp"] = {"$gt": params.since}

        if params.until:
            if "source.timestamp" not in cozystack_query_filters:
                cozystack_query_filters["source.timestamp"] = {}

            cozystack_query_filters["source.timestamp"]["$lte"] = params.until

        cozystack_sort_order = (
            SortDirectionEnum.ASC if params.ascending else SortDirectionEnum.DESC
        )

        cozystack_query_sort = [
            {"source.timestamp": cozystack_sort_order},
            {"source.id": cozystack_sort_order},
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
        self, params: RalphStatementsQuery, target: Optional[str] = None
    ) -> StatementQueryResult:
        """Return the results of a statements query using xAPI parameters."""
        query = self.get_query(params)

        try:
            response = list(
                self.read(query=query, target=target, chunk_size=params.limit)
            )

        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CozyStack")
            raise error

        search_after = query.bookmark if query.next else None

        return StatementQueryResult(
            statements=[document["source"] for document in response],
            search_after=search_after,
        )

    def query_statements_by_ids(
        self, ids: List[str], target: Optional[str] = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""
        query = self.query_class(selector={"source.id": {"$in": ids}})

        try:
            response = self.read(query=query, target=target)
            yield from (document["source"] for document in response)

        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from CozyStack")
            raise error

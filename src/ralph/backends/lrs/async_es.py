"""Asynchronous Elasticsearch LRS backend for Ralph."""

import logging
from collections.abc import AsyncIterator, Sequence

from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.lrs.base import (
    BaseAsyncLRSBackend,
    RalphStatementsQuery,
    StatementQueryResult,
    ids_adapter,
    include_extra_adapter,
    params_adapter,
    target_adapter,
)
from ralph.backends.lrs.es import ESLRSBackend, ESLRSBackendSettings
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class AsyncESLRSBackend(BaseAsyncLRSBackend[ESLRSBackendSettings], AsyncESDataBackend):
    """Asynchronous Elasticsearch LRS backend implementation."""

    async def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        query = ESLRSBackend.get_query(params=params)
        try:
            statements = [
                document["_source"]["statement"]
                async for document in self.read(
                    query=query, target=target, chunk_size=params.limit
                )
            ]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

        return StatementQueryResult(
            statements=statements,
            pit_id=query.pit.id,
            search_after="|".join(query.search_after) if query.search_after else "",
        )

    async def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> AsyncIterator[dict]:
        """Yield statements with matching ids from the backend."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        query = self.query_class(query={"terms": {"_id": ids}})
        try:
            async for document in self.read(query=query, target=target):
                if include_extra:
                    yield document["_source"]
                else:
                    yield document["_source"]["statement"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from Elasticsearch")
            raise error

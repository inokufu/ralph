"""Async MongoDB LRS backend for Ralph."""

import logging
from collections.abc import AsyncIterator, Sequence

from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.lrs.base import (
    BaseAsyncLRSBackend,
    RalphStatementsQuery,
    StatementQueryResult,
    ids_adapter,
    include_extra_adapter,
    params_adapter,
    target_adapter,
)
from ralph.backends.lrs.mongo import MongoLRSBackend, MongoLRSBackendSettings
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class AsyncMongoLRSBackend(
    BaseAsyncLRSBackend[MongoLRSBackendSettings], AsyncMongoDataBackend
):
    """Async MongoDB LRS backend implementation."""

    async def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        query = MongoLRSBackend.get_query(params)
        try:
            mongo_response = [
                document
                async for document in self.read(
                    query=query, target=target, chunk_size=params.limit
                )
            ]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from async MongoDB")
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

    async def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> AsyncIterator[dict]:
        """Yield statements with matching ids from the backend."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        query = self.query_class(filter={"_source.statement.id": {"$in": ids}})
        try:
            async for document in self.read(query=query, target=target):
                if include_extra:
                    yield document["_source"]
                else:
                    yield document["_source"]["statement"]
        except (BackendException, BackendParameterException) as error:
            logger.error("Failed to read from MongoDB")
            raise error

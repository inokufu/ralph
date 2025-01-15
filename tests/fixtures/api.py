"""Test fixtures related to the API."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ralph.api import app


@pytest.mark.anyio
@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient]:
    """Return an AsyncClient for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-Experience-API-Version": "1.0.3"},
    ) as async_client:
        yield async_client

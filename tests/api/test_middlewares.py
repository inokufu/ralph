"""Tests for middlewares of the Ralph API."""

from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from ralph.api import app

from ..helpers import configure_env_for_mock_basic_auth, mock_statement


@pytest.mark.anyio
async def test_x_experience_api_version_header(
    monkeypatch, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """
    Test X-Experience-API-Version header is checked in request and included in response.
    """
    configure_env_for_mock_basic_auth(monkeypatch)

    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=1)).isoformat()),
        mock_statement(timestamp=(datetime.now()).isoformat()),
    ]

    insert_statements_and_monkeypatch_backend(statements)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    ) as client:
        # Check for 400 status code when X-Experience-API-Version header is not included
        response = await client.get(
            "/xAPI/statements/",
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Missing X-Experience-API-Version header"}
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"

        # Check that X-Experience-API-Version header is included in response
        response = await client.get(
            "/xAPI/statements/",
            headers={"X-Experience-API-Version": "1.0.3"},
        )

        assert response.status_code == 200
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"

        # Check for 400 status code when X-Experience-API-Version header
        # is included but unsupported
        response = await client.get(
            "/xAPI/statements/",
            headers={"X-Experience-API-Version": "1.0.4"},
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid X-Experience-API-Version header"}
        assert "X-Experience-API-Version" in response.headers
        assert response.headers["X-Experience-API-Version"] == "1.0.3"

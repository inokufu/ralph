"""Tests for the api.auth.oidc module."""

import pytest
import responses
from fastapi import HTTPException
from pydantic import TypeAdapter

from ralph.api.auth.cozy import (
    decode_auth_token,
    model_validate_cozy_id_token,
    validate_auth_against_cozystack,
)
from ralph.models.xapi.base.agents import BaseXapiAgentWithOpenId

from tests.fixtures.auth import mock_oidc_user
from tests.fixtures.backends import (
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_clickhouse_test_backend,
    get_cozystack_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)
from tests.helpers import (
    configure_env_for_mock_oidc_auth,
    mock_statement,
)

TEST_AUTH_TOKEN = (
    "Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb3p5LnJhbHBoLWNvenktc3RhY"
    "2stMTo4MDgwIiwic3ViIjoibXljb3p5YXBwIiwiYXVkIjpbImFwcCJdLCJpYXQiOjE3MzA5OTA5MjgsIn"
    "Nlc3Npb25faWQiOiI0N2I1OTJmNjg5Y2ViZDY3ZTdlODhjYmU5NTAwMjhmYiJ9.IJzZfN4_sOb4EtX6Nx"
    "UL60bcFCsBetaDlwtpv1FWMpUPMJ9MO2ihK-V2YiczsWCw3EMralijvEPlbWlZsU2u6Q"
)

TEST_DECODED_TOKEN = {
    "iss": "cozy.ralph-cozy-stack-1:8080",
    "sub": "mycozyapp",
    "aud": ["app"],
    "iat": 1730990928,
    "session_id": "47b592f689cebd67e7e88cbe950028fb",
}

TEST_COZY_ID_TOKEN = model_validate_cozy_id_token(TEST_DECODED_TOKEN)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "bad_auth_token",
    [None, 123, "abcd", "Bearer abcd"],
)
async def test_decode_bad_auth_token(bad_auth_token):
    with pytest.raises(HTTPException) as exc:
        decode_auth_token(bad_auth_token)
        assert exc.status_code == 401
        assert exc.detail == "Could not validate credentials"


@pytest.mark.anyio
async def test_decode_auth_token():
    decoded_token = decode_auth_token(TEST_AUTH_TOKEN)
    assert decoded_token == TEST_DECODED_TOKEN


@pytest.mark.anyio
@pytest.mark.parametrize(
    "bad_decoded_token",
    [
        None,
        123,
        "abcd",
        {},
        {k: v for k, v in TEST_DECODED_TOKEN.items() if k != "iss"},
    ],
)
async def test_model_validate_bad_cozy_id_token(bad_decoded_token):
    with pytest.raises(HTTPException) as exc:
        model_validate_cozy_id_token(bad_decoded_token)
        assert exc.status_code == 401
        assert exc.detail == "Could not validate credentials"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "decoded_token",
    [TEST_DECODED_TOKEN, {k: v for k, v in TEST_DECODED_TOKEN.items() if k != "sub"}],
)
async def test_model_validate_cozy_id_token(decoded_token):
    id_token = model_validate_cozy_id_token(decoded_token)

    for key in decoded_token:
        assert getattr(id_token, key) == decoded_token[key]


@pytest.mark.anyio
async def test_validate_bad_auth_against_cozystack():
    decoded_token = decode_auth_token(TEST_AUTH_TOKEN)
    id_token = model_validate_cozy_id_token(decoded_token)

    with pytest.raises(HTTPException) as exc:
        validate_auth_against_cozystack(id_token, TEST_AUTH_TOKEN)
        assert exc.status_code == 401
        assert exc.detail == "Could not validate credentials"


@pytest.mark.anyio
async def test_validate_auth_against_cozystack(cozy_auth_token):
    x_auth_token = f"Bearer {cozy_auth_token}"

    decoded_token = decode_auth_token(x_auth_token)
    id_token = model_validate_cozy_id_token(decoded_token)

    assert not id_token.iss.startswith("http")

    cozy_auth_data = validate_auth_against_cozystack(id_token, x_auth_token)

    assert str(cozy_auth_data.instance_url) == "http://cozy.ralph-cozy-stack-1:8080/"
    assert cozy_auth_data.token == x_auth_token


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_cozystack_test_backend,
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_auth_cozy_get_whoami_valid(
    client, backend, monkeypatch, cozy_auth_token
):
    """Test a valid CozyStack authentication."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    headers = {"X-Auth-Token": f"Bearer {cozy_auth_token}"}

    response = await client.get("/whoami", headers=headers)

    assert response.status_code == 200

    json_response = response.json()

    assert json_response["agent"] == {
        "openid": "cozy.ralph-cozy-stack-1:8080/cli",
        "objectType": "Agent",
    }

    assert TypeAdapter(BaseXapiAgentWithOpenId).validate_python(json_response["agent"])

    assert sorted(json_response["scopes"]) == [
        "statements/read/mine",
        "statements/write",
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "backend",
    [
        get_cozystack_test_backend,
        get_async_es_test_backend,
        get_async_mongo_test_backend,
        get_es_test_backend,
        get_clickhouse_test_backend,
        get_mongo_test_backend,
    ],
)
async def test_api_auth_cozy_get_whoami_invalid_header(client, backend, monkeypatch):
    """Test CozyStack authentication with invalid request header."""
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend())

    headers = {"X-Auth-Token": "Bearer abcd"}

    response = await client.get("/whoami", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.anyio
@responses.activate
async def test_api_auth_oidc_post_statements_to_cozystack_backend(client, monkeypatch):
    """Test a valid OpenId Connect authentication."""
    configure_env_for_mock_oidc_auth(monkeypatch)
    oidc_token = mock_oidc_user(scopes=["all", "profile/read"])

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_cozystack_test_backend()
    )
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"Authorization": f"Bearer {oidc_token}"},
        json=statement,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Can't validate Cozy authentication data"}

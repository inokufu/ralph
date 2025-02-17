"""Tests for the PUT statements endpoint of the Ralph API."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from ralph.backends.cozystack import CozyStackClient
from ralph.exceptions import BackendException

from tests.fixtures.backends import (
    get_cozystack_test_backend,
)
from tests.helpers import (
    assert_statement_get_responses_are_equivalent,
    configure_env_for_mock_cozy_auth,
    mock_statement,
    statements_are_equivalent,
    string_is_date,
)


@pytest.mark.anyio
async def test_api_statements_put_single_statement_directly(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the put statements API route with one statement."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 204

    # get all
    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200

    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )

    # get by id
    response = await client.get(
        f"/xAPI/statements/?statementId={statement["id"]}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert statements_are_equivalent(response.json(), statement)


@pytest.mark.anyio
async def test_api_statements_put_bad_statement(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route with one statement."""
    init_cozystack_db_and_monkeypatch_backend()

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json={"abc": 123},
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_api_statements_put_enriching_without_existing_values(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that statements are properly enriched when statement provides no values."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )
    assert response.status_code == 204

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    statement = response.json()["statements"][0]

    # Test pre-processing: id
    assert "id" in statement
    assert statement

    # Test pre-processing: timestamp
    assert "timestamp" in statement
    assert string_is_date(statement["timestamp"])

    # Test pre-processing: stored
    assert "stored" in statement
    assert string_is_date(statement["stored"])

    # Test pre-processing: authority
    assert "authority" in statement
    assert statement["authority"] == {
        "openid": "cozy.ralph-cozy-stack-1:8080/cli",
        "objectType": "Agent",
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "field,value,status",
    [
        ("timestamp", "2022-06-22T08:31:38Z", 204),
        ("stored", "2022-06-22T08:31:38Z", 204),
        (
            "authority",
            {"openid": "cozy.ralph-cozy-stack-1:8080/cli", "objectType": "Agent"},
            204,
        ),
    ],
)
async def test_api_statements_put_enriching_with_existing_values(  # noqa: PLR0913
    client: AsyncClient,
    field: str,
    value: Any,
    status: int,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that statements are properly enriched when values are provided."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    # Add the field to be tested
    statement[field] = value

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == status

    # Check that values match when they should
    if status == 204:
        response = await client.get(
            "/xAPI/statements/",
            headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        )
        statement = response.json()["statements"][0]

        # Test enriching
        assert field in statement
        if field == "stored":
            # Check that stored value was overwritten
            assert statement[field] != value
        else:
            assert statement[field] == value


@pytest.mark.anyio
async def test_api_statements_put_single_statement_no_trailing_slash(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that the statements endpoint also works without the trailing slash."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 204


@pytest.mark.anyio
async def test_api_statements_put_id_mismatch(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the put statements API route when the statementId doesn't match."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement(id_=str(uuid4()))

    different_statement_id = str(uuid4())
    response = await client.put(
        f"/xAPI/statements/?statementId={different_statement_id}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "xAPI statement id does not match given statementId"
    }


@pytest.mark.anyio
async def test_api_statements_put_list_of_one(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that we fail on PUTs with a list, even if it's one statement."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=[statement],
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_api_statements_put_duplicate_of_existing_statement(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the put statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    # Put the statement once.
    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )
    assert response.status_code == 204

    # Put the statement twice, trying to change the timestamp, which is not allowed
    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=dict(statement, **{"timestamp": "2023-03-15T14:07:51Z"}),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A different statement already exists with the same ID"
    }

    response = await client.get(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert statements_are_equivalent(response.json(), statement)


@pytest.mark.anyio
async def test_api_statements_put_with_failure_during_storage(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test the put statements API route with a failure happening during storage."""
    configure_env_for_mock_cozy_auth(monkeypatch)

    def write_mock(*args, **kwargs):
        """Raise an exception. Mocks the database.write method."""
        raise BackendException()

    # set up a fresh database
    cozystack_custom()
    backend_instance = get_cozystack_test_backend()
    monkeypatch.setattr(backend_instance, "write", write_mock)
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statement indexation failed"}


@pytest.mark.anyio
async def test_api_statements_put_with_a_failure_during_id_query(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test the put statements API route with a failure during query execution."""
    configure_env_for_mock_cozy_auth(monkeypatch)

    def query_statements_by_ids_mock(*args, **kwargs):
        """Raise an exception. Mock the database.query_statements_by_ids method."""
        raise BackendException()

    # set up a fresh database
    cozystack_custom()
    backend_instance = get_cozystack_test_backend()
    monkeypatch.setattr(
        backend_instance, "query_statements_by_ids", query_statements_by_ids_mock
    )
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
async def test_api_statements_put_without_forwarding(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the put statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """
    init_cozystack_db_and_monkeypatch_backend()

    spy = {}

    def spy_mock_forward_xapi_statements(_):
        """Mock the forward_xapi_statements; spies over whether it has been called."""
        spy["error"] = "forward_xapi_statements should not have been called!"

    monkeypatch.setattr(
        "ralph.api.routers.statements.forward_xapi_statements",
        spy_mock_forward_xapi_statements,
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.get_active_xapi_forwardings", lambda: []
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT", get_cozystack_test_backend()
    )

    statement = mock_statement()

    response = await client.put(
        f"/xAPI/statements/?statementId={statement['id']}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 204

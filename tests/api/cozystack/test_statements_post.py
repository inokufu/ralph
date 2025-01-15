"""Tests for the POST statements endpoint of the Ralph API."""

import re
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
    mock_statement,
    string_is_date,
    string_is_uuid,
)


@pytest.mark.anyio
async def test_api_statements_post_invalid_parameters(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that using invalid parameters returns the proper status code."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    # Check for 400 status code when unknown parameters are provided
    response = await client.post(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }


@pytest.mark.anyio
async def test_api_statements_post_single_statement_directly(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route with one statement."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
async def test_api_statements_post_bad_statement(
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
async def test_api_statements_post_enriching_without_existing_values(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that statements are properly enriched when statement provides no values."""
    init_cozystack_db_and_monkeypatch_backend()

    statement = {
        "actor": {
            "account": {
                "homePage": "https://example.com/homepage/",
                "name": str(uuid4()),
            },
            "objectType": "Agent",
        },
        "object": {"id": "https://example.com/object-id/1/"},
        "verb": {"id": "https://example.com/verb-id/1/"},
    }

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 200

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    statement = response.json()["statements"][0]

    # Test pre-processing: id
    assert "id" in statement
    assert string_is_uuid(statement["id"])

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
        ("id", str(uuid4()), 200),
        ("timestamp", "2022-06-22T08:31:38Z", 200),
        ("stored", "2022-06-22T08:31:38Z", 200),
        (
            "authority",
            {"openid": "cozy.ralph-cozy-stack-1:8080/cli", "objectType": "Agent"},
            200,
        ),
    ],
)
async def test_api_statements_post_enriching_with_existing_values(  # noqa: PLR0913
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

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == status

    # Check that values match when they should
    if status == 200:
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
async def test_api_statements_post_single_statement_no_trailing_slash(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test that the statements endpoint also works without the trailing slash."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]


@pytest.mark.anyio
async def test_api_statements_post_list_of_one(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route with one statement in a list."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=[statement],
    )

    assert response.status_code == 200
    assert response.json() == [statement["id"]]

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
async def test_api_statements_post_list(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route with two statements in a list."""
    init_cozystack_db_and_monkeypatch_backend()

    statement_1 = mock_statement(timestamp="2022-03-15T14:07:52Z")

    # Note the second statement has no preexisting ID
    statement_2 = mock_statement(timestamp="2022-03-15T14:07:51Z")
    statement_2.pop("id")

    statements = [statement_1, statement_2]

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statements,
    )

    assert response.status_code == 200
    assert response.json()[0] == statements[0]["id"]
    regex = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    generated_id = response.json()[1]
    assert regex.match(generated_id)

    get_response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert get_response.status_code == 200

    # Update statements with the generated id.
    statements[1] = dict(statements[1], **{"id": generated_id})

    assert_statement_get_responses_are_equivalent(
        get_response.json(), {"statements": statements}
    )


@pytest.mark.anyio
async def test_api_statements_post_list_with_duplicates(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route with duplicate statement IDs should fail."""
    init_cozystack_db_and_monkeypatch_backend()
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=[statement, statement],
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Duplicate statement IDs in the list of statements"
    }

    # The failure should imply no statement insertion.
    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_post_list_with_duplicate_of_existing_statement(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the post statements API route, given a statement that already exist in the
    database (has the same ID), should fail.
    """
    init_cozystack_db_and_monkeypatch_backend()

    statement_uuid = str(uuid4())
    statement = mock_statement(id_=statement_uuid)

    # Post the statement once.
    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )
    assert response.status_code == 200
    assert response.json() == [statement_uuid]

    # Post the statement twice, the data is identical so it should succeed but not
    # include the ID in the response as it wasn't inserted.
    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )
    assert response.status_code == 204

    # Post the statement again, trying to change the timestamp which is not allowed.
    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=[dict(statement, **{"timestamp": "2023-03-15T14:07:51Z"})],
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": f"Differing statements already exist with the same ID: "
        f"{statement_uuid}"
    }

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 200
    assert_statement_get_responses_are_equivalent(
        response.json(), {"statements": [statement]}
    )


@pytest.mark.anyio
async def test_api_statements_post_with_failure_during_storage(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test the post statements API route with a failure happening during storage."""

    async def write_mock(*args, **kwargs):
        """Raise an exception. Mocks the database.write method."""
        raise BackendException()

    # set up a fresh database
    cozystack_custom()
    backend_instance = get_cozystack_test_backend()
    monkeypatch.setattr(backend_instance, "write", write_mock)
    monkeypatch.setattr("ralph.api.routers.statements.BACKEND_CLIENT", backend_instance)
    statement = mock_statement()

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Statements bulk indexation failed"}


@pytest.mark.anyio
async def test_api_statements_post_with_failure_during_id_query(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test the post statements API route with a failure during query execution."""

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

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
async def test_api_statements_post_list_without_forwarding(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test the post statements API route, given an empty forwarding configuration,
    should not start the forwarding background task.
    """
    # set up a fresh database
    cozystack_custom()

    spy = {}

    async def spy_mock_forward_xapi_statements(_):
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

    response = await client.post(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        json=statement,
    )

    assert response.status_code == 200
    assert "error" not in spy

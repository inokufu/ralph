"""Tests for the GET statements endpoint of the Ralph API."""

import json
from collections.abc import Callable
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote_plus, urlparse

import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch

from ralph.backends.cozystack import CozyStackClient
from ralph.exceptions import BackendException

from tests.fixtures.backends import get_cozystack_test_backend
from tests.helpers import (
    configure_env_for_mock_cozy_auth,
    mock_activity,
    mock_agent,
    mock_statement,
)


@pytest.mark.anyio
async def test_api_statements_get(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route without any filters set up."""
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
        )
        for i in range(3)
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    # Confirm that calling this with and without the trailing slash both work
    for path in ("/xAPI/statements", "/xAPI/statements/"):
        response = await client.get(
            path,
            headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        )

        assert response.status_code == 200
        assert response.json() == {"statements": statements}


@pytest.mark.anyio
async def test_api_statements_get_ascending(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "ascending" query parameter, should
    return statements in ascending order by their timestamp.
    """
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
        )
        for i in range(3)
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?ascending=true",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": list(reversed(statements))}


@pytest.mark.anyio
async def test_api_statements_get_ascending_no_bool(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "ascending" query parameter, should
    return statements in ascending order by their timestamp.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?ascending=toto",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400

    error = response.json()["detail"][0]
    assert error["type"] == "bool_parsing"
    assert error["loc"] == ["query", "ascending"]


@pytest.mark.anyio
async def test_api_statements_get_by_statement_id(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "statementId" query parameter, should
    return a list of statements matching the given statementId.
    """
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
        )
        for i in range(3)
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        f"/xAPI/statements/?statementId={statements[1]["id"]}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == statements[1]


@pytest.mark.anyio
async def test_api_statements_get_by_statement_id_no_uuid(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "statementId" query parameter, should
    return a list of statements matching the given statementId.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?statementId=abc",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400

    error = response.json()["detail"][0]
    assert error["type"] == "uuid_parsing"
    assert error["loc"] == ["query", "statementId"]


@pytest.mark.anyio
async def test_api_statements_get_by_verb(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "verb" query parameter, should
    return a list of statements filtered by the given verb id.
    """
    statements = [
        mock_statement(
            timestamp=datetime.now().isoformat(),
            verb={"id": "http://adlnet.gov/expapi/verbs/experienced"},
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
            verb={"id": "http://adlnet.gov/expapi/verbs/played"},
        ),
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_verb_unknown_iri(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "verb" query parameter, should
    return a list of statements filtered by the given verb id.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/experienced"},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/played"},
        },
    ]
    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/tested"),
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_get_by_verb_no_iri(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "verb" query parameter, should
    return a list of statements filtered by the given verb id.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/experienced"},
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "verb": {"id": "http://adlnet.gov/expapi/verbs/played"},
        },
    ]
    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?verb=tested",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, 'tested' is not a valid 'IRI'."
    )


@pytest.mark.anyio
async def test_api_statements_get_by_activity(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """
    statements = [mock_statement(object=mock_activity(i)) for i in range(3)]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        f"/xAPI/statements/?activity={statements[1]["object"]["id"]}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_activity_unknown_iri(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """

    activity_0 = mock_activity(0)
    activity_1 = mock_activity(1)

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "object": activity_0,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "object": activity_1,
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?activity=http://example.com/unknown",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_get_by_activity_no_iri(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """

    activity_0 = mock_activity(0)
    activity_1 = mock_activity(1)

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "object": activity_0,
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
            "object": activity_1,
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?activity=unknown",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, 'unknown' is not a valid 'IRI'."
    )


@pytest.mark.anyio
async def test_api_statements_get_since_timestamp(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "since" query parameter, should
    return a list of statements filtered by the given timestamp.
    """
    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=1)).isoformat()),
        mock_statement(timestamp=(datetime.now()).isoformat()),
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    # since timestamp between the two statements' timestamp
    since = (datetime.now() - timedelta(minutes=30)).isoformat()

    response = await client.get(
        f"/xAPI/statements/?since={since}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}

    # since timestamp after the two statements' timestamp
    since = (datetime.now() + timedelta(minutes=30)).isoformat()

    response = await client.get(
        f"/xAPI/statements/?since={since}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_get_since_no_timestamp(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a "since" query parameter, should
    return a list of statements filtered by the given timestamp.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?since=abc",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400

    error = response.json()["detail"][0]
    assert error["type"] == "datetime_from_date_parsing"
    assert error["loc"] == ["query", "since"]


@pytest.mark.anyio
async def test_api_statements_get_until_timestamp(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "until" query parameter,
    should return a list of statements filtered by the given timestamp.
    """
    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=1)).isoformat()),
        mock_statement(timestamp=(datetime.now()).isoformat()),
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    # until timestamp between the two statements' timestamp
    until = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = await client.get(
        f"/xAPI/statements/?until={until}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # until timestamp before the two statements' timestamp
    until = (datetime.now() - timedelta(hours=2)).isoformat()
    response = await client.get(
        f"/xAPI/statements/?until={until}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": []}


@pytest.mark.anyio
async def test_api_statements_get_until_no_timestamp(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given an "until" query parameter,
    should return a list of statements filtered by the given timestamp.
    """

    statements = [
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?until=abc",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 400

    error = response.json()["detail"][0]
    assert error["type"] == "datetime_from_date_parsing"
    assert error["loc"] == ["query", "until"]


@pytest.mark.anyio
async def test_api_statements_get_with_pagination(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a request leading to more results than
    can fit on the first page, should return a list of statements non-exceeding the page
    limit and include a "more" property with a link to get the next page of results.
    """
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=5 - i)).isoformat())
        for i in range(5)
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[4], statements[3]]

    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)

    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("pit_id", "search_after"))

    # Second response gets the missing result from the first response.
    second_response = await client.get(
        first_response.json()["more"],
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert second_response.status_code == 200
    assert second_response.json()["statements"] == [statements[2], statements[1]]

    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)

    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("pit_id", "search_after"))

    # Third response gets the missing result from the second response
    third_response = await client.get(
        second_response.json()["more"],
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert third_response.status_code == 200
    assert third_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_pagination_and_query(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a request with a query parameter
    leading to more results than can fit on the first page, should return a list
    of statements non-exceeding the page limit and include a "more" property with
    a link to get the next page of results.
    """
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.RUNSERVER_MAX_SEARCH_HITS_COUNT", 2
    )

    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=3 - i)).isoformat(),
            verb={
                "id": "https://w3id.org/xapi/video/verbs/played",
                "display": {"en-US": "played"},
            },
        )
        for i in range(3)
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = await client.get(
        "/xAPI/statements/?verb="
        + quote_plus("https://w3id.org/xapi/video/verbs/played"),
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert first_response.status_code == 200
    assert first_response.json()["statements"] == [statements[2], statements[1]]
    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)
    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("verb", "pit_id", "search_after"))

    # Second response gets the missing result from the first response.
    second_response = await client.get(
        first_response.json()["more"],
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_no_matching_statement(
    client: AsyncClient,
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_token: str,
):
    """Test the get statements API route, given a query yielding no matching statement,
    should return an empty list.
    """
    statements = [
        mock_statement(
            id_="be67b160-d958-4f51-b8b8-1892002dbac6",
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            id_="72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            timestamp=(datetime.now()).isoformat(),
        ),
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Statement not found"}


@pytest.mark.anyio
async def test_api_statements_get_with_database_query_failure(
    client: AsyncClient, monkeypatch: MonkeyPatch, cozy_auth_token: str
):
    """Test the get statements API route, given a query raising a BackendException,
    should return an error response with HTTP code 500.
    """
    configure_env_for_mock_cozy_auth(monkeypatch)

    def mock_query_statements(*_, **__):
        """Mocks the BACKEND_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT.query_statements",
        mock_query_statements,
    )

    response = await client.get(
        "/xAPI/statements/",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
@pytest.mark.parametrize("id_param", ["statementId", "voidedStatementId"])
async def test_api_statements_get_invalid_query_parameters(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
    id_param: str,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_token: str,
):
    """Test error response for invalid query parameters"""
    configure_env_for_mock_cozy_auth(monkeypatch)

    id_1 = "be67b160-d958-4f51-b8b8-1892002dbac6"
    id_2 = "66c81e98-1763-4730-8cfc-f5ab34f1bad5"

    # Check for 400 status code when unknown parameters are provided
    response = await client.get(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }

    # Check for 400 status code when a negative limit parameter is provided
    response = await client.get(
        "/xAPI/statements/?limit=-1",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when both statementId and voidedStatementId are provided
    response = await client.get(
        f"/xAPI/statements/?statementId={id_1}&voidedStatementId={id_2}",
        headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when invalid parameters are provided with a statementId
    for invalid_param, value in [
        ("activity", mock_activity()["id"]),
        ("agent", json.dumps(mock_agent("mbox", 1))),
        ("verb", "verb_1"),
    ]:
        response = await client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{invalid_param}={value}",
            headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": (
                "Querying by id only accepts `attachments` and `format` as "
                "extra parameters"
            )
        }

    cozystack_custom()
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    monkeypatch.setattr(backend_client_class_path, get_cozystack_test_backend())

    # Check for NO 400 status code when statementId is passed with authorized parameters
    for valid_param, value in [("format", "ids"), ("attachments", "true")]:
        response = await client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{valid_param}={value}",
            headers={"X-Auth-Token": f"Bearer {cozy_auth_token}"},
        )
        assert response.status_code != 400

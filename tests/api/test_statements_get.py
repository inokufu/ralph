"""Tests for the GET statements endpoint of the Ralph API."""

import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs, quote_plus, urlparse

import pytest
import responses

from ralph.api.auth.basic import get_basic_auth_user
from ralph.conf import AuthBackend
from ralph.exceptions import BackendException

from tests.fixtures.backends import get_es_test_backend

from ..fixtures.auth import AUDIENCE, ISSUER_URI, mock_basic_auth_user, mock_oidc_user
from ..fixtures.statements import insert_es_statements
from ..helpers import mock_activity, mock_agent, mock_statement


@pytest.mark.anyio
@pytest.mark.parametrize(
    "ifi",
    [
        "mbox",
        "mbox_sha1sum",
        "openid",
        "account_same_home_page",
        "account_different_home_page",
    ],
)
async def test_api_statements_get_mine(
    client, monkeypatch, fs, insert_statements_and_monkeypatch_backend, ifi
):
    """(Security) Test that the get statements API route, given a "mine=True"
    query parameter returns a list of statements filtered by authority.
    """

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_1_bis = mock_agent(
            "account", 1, home_page_id=1, name="myname", use_object_type=False
        )
        agent_2 = mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_1_bis = mock_agent(
            "account", 1, home_page_id=1, name="myname", use_object_type=False
        )
        agent_2 = mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = mock_agent(ifi, 1)
        agent_1_bis = mock_agent(ifi, 1, name="myname", use_object_type=False)
        agent_2 = mock_agent(ifi, 2)

    username_1 = "jane"
    password_1 = "janepwd"
    scopes = []

    credentials_1_bis = mock_basic_auth_user(
        fs, username_1, password_1, scopes, agent_1_bis
    )

    # Clear cache before each test iteration
    get_basic_auth_user.cache_clear()

    statements = [
        mock_statement(
            actor=agent_1,
            authority=agent_1,
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            actor=agent_1, authority=agent_2, timestamp=datetime.now().isoformat()
        ),
    ]

    insert_statements_and_monkeypatch_backend(statements)

    # No restriction on "mine" (implicit) : Return all statements
    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # No restriction on "mine" (explicit) : Return all statements
    response = await client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1], statements[0]]}

    # Only fetch mine (explicit) : Return filtered statements
    response = await client.get(
        "/xAPI/statements/?mine=True",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Only fetch mine (implicit with RALPH_LRS_RESTRICT_BY_AUTHORITY=True): Return
    # filtered statements
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Only fetch mine (implicit) with contradictory user request: Return filtered
    # statements
    response = await client.get(
        "/xAPI/statements/?mine=False",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}

    # Fetch "mine" by id with a single forbidden statement : Return 404 not found
    response = await client.get(
        f"/xAPI/statements/?statementId={statements[1]["id"]}&mine=True",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Statement not found"}

    # Check that invalid parameters returns an error
    response = await client.get(
        "/xAPI/statements/?mine=BigBoat",
        headers={"Authorization": f"Basic {credentials_1_bis}"},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_api_statements_get(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route without any filters set up."""
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=3 - i)).isoformat(),
        )
        for i in range(3)
    ]

    insert_statements_and_monkeypatch_backend(statements)

    # Confirm that calling this with and without the trailing slash both work
    for path in ("/xAPI/statements", "/xAPI/statements/"):
        response = await client.get(
            path, headers={"Authorization": f"Basic {basic_auth_credentials}"}
        )

        assert response.status_code == 200
        assert response.json() == {"statements": list(reversed(statements))}


@pytest.mark.anyio
async def test_api_statements_get_from_target(
    fs, client, insert_statements_and_monkeypatch_backend
):
    """Test the get statements API route with a different target."""

    # Create one user with a specific target
    username = "jane"
    password = "janepwd"
    scopes = []
    target = "custom_target"
    agent = mock_agent("account", 1, home_page_id=1)

    credentials = mock_basic_auth_user(fs, username, password, scopes, agent, target)

    # Clear cache before each test iteration
    get_basic_auth_user.cache_clear()

    # Insert statements into the default target
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
        ),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    # Insert statements into the custom target
    custom_target = "custom_target"

    statements_custom = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
        ),
    ]
    insert_statements_and_monkeypatch_backend(statements_custom, custom_target)

    # Confirm that calling this for a user with a custom target works retrieved
    # statements from custom target only
    response = await client.get(
        "/xAPI/statements",
        headers={"Authorization": f"Basic {credentials}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "statements": [statements_custom[1], statements_custom[0]]
    }


@pytest.mark.anyio
async def test_api_statements_get_ascending(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "ascending" query parameter, should
    return statements in ascending order by their timestamp.
    """
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
        ),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?ascending=true",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0], statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_statement_id(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a "statementId" query parameter, should
    return a list of statements matching the given statementId.
    """

    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
        ),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        f"/xAPI/statements/?statementId={statements[1]["id"]}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == statements[1]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "ifi",
    [
        "mbox",
        "mbox_sha1sum",
        "openid",
        "account_same_home_page",
        "account_different_home_page",
    ],
)
async def test_api_statements_get_by_agent(
    client, ifi, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "agent" query parameter, should
    return a list of statements filtered by the given agent.
    """

    # Create two distinct agents
    if ifi == "account_same_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_2 = mock_agent("account", 2, home_page_id=1)
    elif ifi == "account_different_home_page":
        agent_1 = mock_agent("account", 1, home_page_id=1)
        agent_2 = mock_agent("account", 1, home_page_id=2)
    else:
        agent_1 = mock_agent(ifi, 1)
        agent_2 = mock_agent(ifi, 2)

    statements = [
        mock_statement(actor=agent_1, authority=agent_1),
        mock_statement(actor=agent_2, authority=agent_1),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        f"/xAPI/statements/?agent={quote_plus(json.dumps(agent_1))}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_by_verb(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
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

    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?verb=" + quote_plus("http://adlnet.gov/expapi/verbs/played"),
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_by_activity(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "activity" query parameter, should
    return a list of statements filtered by the given activity id.
    """

    activity_0 = mock_activity(0)
    activity_1 = mock_activity(1)

    statements = [
        mock_statement(
            timestamp=datetime.now().isoformat(),
            object=activity_0,
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
            object=activity_1,
        ),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        f"/xAPI/statements/?activity={activity_1["id"]}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_since_timestamp(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a "since" query parameter, should
    return a list of statements filtered by the given timestamp.
    """
    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=1)).isoformat()),
        mock_statement(timestamp=(datetime.now()).isoformat()),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    since = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = await client.get(
        f"/xAPI/statements/?since={since}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[1]]}


@pytest.mark.anyio
async def test_api_statements_get_until_timestamp(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given an "until" query parameter,
    should return a list of statements filtered by the given timestamp.
    """
    statements = [
        mock_statement(timestamp=(datetime.now() - timedelta(hours=1)).isoformat()),
        mock_statement(timestamp=(datetime.now()).isoformat()),
    ]
    insert_statements_and_monkeypatch_backend(statements)

    until = (datetime.now() - timedelta(minutes=30)).isoformat()
    response = await client.get(
        f"/xAPI/statements/?until={until}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 200
    assert response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_pagination(
    client,
    monkeypatch,
    insert_statements_and_monkeypatch_backend,
    basic_auth_credentials,
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
    insert_statements_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
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
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json()["statements"] == [statements[2], statements[1]]
    more = urlparse(first_response.json()["more"])
    more_query_params = parse_qs(more.query)
    assert more.path == "/xAPI/statements/"
    assert all(key in more_query_params for key in ("pit_id", "search_after"))

    # Third response gets the missing result from the first response
    third_response = await client.get(
        second_response.json()["more"],
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert third_response.status_code == 200
    assert third_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_pagination_and_query(
    client,
    monkeypatch,
    insert_statements_and_monkeypatch_backend,
    basic_auth_credentials,
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

    insert_statements_and_monkeypatch_backend(statements)

    # First response gets the first two results, with a "more" entry as
    # we have more results to return on a later page.
    first_response = await client.get(
        "/xAPI/statements/?verb="
        + quote_plus("https://w3id.org/xapi/video/verbs/played"),
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
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
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert second_response.status_code == 200
    assert second_response.json() == {"statements": [statements[0]]}


@pytest.mark.anyio
async def test_api_statements_get_with_no_matching_statement(
    client, insert_statements_and_monkeypatch_backend, basic_auth_credentials
):
    """Test the get statements API route, given a query yielding no matching statement,
    should return an empty list.
    """
    statements = [
        mock_statement(),
        mock_statement(),
    ]

    insert_statements_and_monkeypatch_backend(statements)

    response = await client.get(
        "/xAPI/statements/?statementId=66c81e98-1763-4730-8cfc-f5ab34f1bad5",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Statement not found"}


@pytest.mark.anyio
async def test_api_statements_get_with_database_query_failure(
    client, basic_auth_credentials, monkeypatch
):
    """Test the get statements API route, given a query raising a BackendException,
    should return an error response with HTTP code 500.
    """

    def mock_query_statements(*_, **__):
        """Mocks the BACKEND_CLIENT.query_statements method."""
        raise BackendException()

    monkeypatch.setattr(
        "ralph.api.routers.statements.BACKEND_CLIENT.query_statements",
        mock_query_statements,
    )

    response = await client.get(
        "/xAPI/statements/",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "xAPI statements query failed"}


@pytest.mark.anyio
@pytest.mark.parametrize("id_param", ["statementId", "voidedStatementId"])
async def test_api_statements_get_invalid_query_parameters(
    client, monkeypatch, es, basic_auth_credentials, id_param
):
    """Test error response for invalid query parameters"""

    id_1 = "be67b160-d958-4f51-b8b8-1892002dbac6"
    id_2 = "66c81e98-1763-4730-8cfc-f5ab34f1bad5"

    # Check for 400 status code when unknown parameters are provided
    response = await client.get(
        "/xAPI/statements/?mamamia=herewegoagain",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "The following parameter is not allowed: `mamamia`"
    }

    # Check for 400 status code when a negative limit parameter is provided
    response = await client.get(
        "/xAPI/statements/?limit=-1",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
    )
    assert response.status_code == 400

    # Check for 400 status code when both statementId and voidedStatementId are provided
    response = await client.get(
        f"/xAPI/statements/?statementId={id_1}&voidedStatementId={id_2}",
        headers={"Authorization": f"Basic {basic_auth_credentials}"},
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
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": (
                "Querying by id only accepts `attachments` and `format` as "
                "extra parameters"
            )
        }

    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    # Check for NO 400 status code when statementId is passed with authorized parameters
    for valid_param, value in [("format", "ids"), ("attachments", "true")]:
        response = await client.get(
            f"/xAPI/statements/?{id_param}={id_1}&{valid_param}={value}",
            headers={"Authorization": f"Basic {basic_auth_credentials}"},
        )
        assert response.status_code != 400


@pytest.mark.anyio
@responses.activate
@pytest.mark.parametrize("auth_method", ["basic", "oidc"])
@pytest.mark.parametrize(
    "scopes,is_authorized",
    [
        (["all"], True),
        (["all/read"], True),
        (["statements/read/mine"], True),
        (["statements/read"], True),
        (["profile/write", "statements/read", "profile/read"], True),
        (["statements/write"], False),
        (["profile/read"], False),
        ([], False),
    ],
)
async def test_api_statements_get_scopes(  # noqa: PLR0913
    client, monkeypatch, fs, es, auth_method, scopes, is_authorized
):
    """Test that getting statements behaves properly according to user scopes."""

    # Scopes settings
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr(
        f"ralph.api.auth.{auth_method}.settings.LRS_RESTRICT_BY_SCOPES", True
    )

    # Authority settings
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    monkeypatch.setattr(
        f"ralph.api.auth.{auth_method}.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )

    # Set up the authentication method
    if auth_method == "basic":
        agent = mock_agent("mbox", 1)
        credentials = mock_basic_auth_user(fs, scopes=scopes, agent=agent)
        headers = {"Authorization": f"Basic {credentials}"}
        get_basic_auth_user.cache_clear()

    elif auth_method == "oidc":
        monkeypatch.setenv("RUNSERVER_AUTH_BACKENDS", "oidc")
        monkeypatch.setattr(
            "ralph.api.auth.settings.RUNSERVER_AUTH_BACKENDS", [AuthBackend.OIDC]
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
            ISSUER_URI,
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
            AUDIENCE,
        )

        sub = "123_oidc"
        iss = "https://iss.example.com"
        agent = {"openid": f"{iss}/{sub}", "objectType": "Agent"}
        oidc_token = mock_oidc_user(sub=sub, scopes=scopes)
        headers = {"Authorization": f"Bearer {oidc_token}"}

        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_ISSUER_URI",
            "http://providerHost:8080/auth/realms/real_name",
        )
        monkeypatch.setattr(
            "ralph.api.auth.oidc.settings.RUNSERVER_AUTH_OIDC_AUDIENCE",
            "http://clientHost:8100",
        )

    # Mock statements
    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
            actor=agent,
            authority=agent,
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
            actor=agent,
            authority=agent,
        ),
    ]

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    # Fetch Statements
    response = await client.get(
        "/xAPI/statements/",
        headers=headers,
    )

    if is_authorized:
        assert response.status_code == 200
        assert response.json() == {"statements": [statements[1], statements[0]]}
    else:
        assert response.status_code == 401
        assert response.json() == {
            "detail": 'Access not authorized to scope: "statements/read/mine".'
        }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "scopes,read_all_access",
    [
        (["all"], True),
        (["all/read", "statements/read/mine"], True),
        (["statements/read"], True),
        (["statements/read/mine"], False),
    ],
)
async def test_api_statements_get_scopes_with_authority(  # noqa: PLR0913
    client, monkeypatch, fs, es, scopes, read_all_access
):
    """Test that restricting by scope and by authority behaves properly.
    Getting statements should be restricted to mine for users which only have
    `statements/read/mine` scope but should not be restricted when the user
    has wider scopes.
    """

    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_AUTHORITY", True
    )
    monkeypatch.setattr(
        "ralph.api.routers.statements.settings.LRS_RESTRICT_BY_SCOPES", True
    )
    monkeypatch.setattr("ralph.api.auth.basic.settings.LRS_RESTRICT_BY_SCOPES", True)
    monkeypatch.setattr("ralph.api.auth.oidc.settings.LRS_RESTRICT_BY_SCOPES", True)

    agent = mock_agent("mbox", 1)
    agent_2 = mock_agent("mbox", 2)
    username = "jane"
    password = "janepwd"
    credentials = mock_basic_auth_user(fs, username, password, scopes, agent)
    headers = {"Authorization": f"Basic {credentials}"}

    get_basic_auth_user.cache_clear()

    statements = [
        mock_statement(
            timestamp=(datetime.now() - timedelta(hours=1)).isoformat(),
            actor=agent,
            authority=agent,
        ),
        mock_statement(
            timestamp=datetime.now().isoformat(),
            actor=agent,
            authority=agent_2,
        ),
    ]

    # NB: scopes are not linked to statements and backends, we therefore test with ES
    backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
    insert_es_statements(es, statements)
    monkeypatch.setattr(backend_client_class_path, get_es_test_backend())

    response = await client.get(
        "/xAPI/statements/",
        headers=headers,
    )

    assert response.status_code == 200

    if read_all_access:
        assert response.json() == {"statements": [statements[1], statements[0]]}
    else:
        assert response.json() == {"statements": [statements[0]]}

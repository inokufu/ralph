"""Tests for Ralph CozyStack LRS backend."""

import logging

import pytest

from ralph.backends.cozystack.exceptions import ExpiredTokenError
from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.backends.lrs.cozystack import CozyStackLRSBackend
from ralph.exceptions import BackendException


def test_backends_lrs_cozystack_default_instantiation(
    monkeypatch: pytest.MonkeyPatch, fs
):
    """Test the `CozyStackLRSBackend` default instantiation."""
    fs.create_file(".env")

    monkeypatch.delenv("RALPH_BACKENDS__LRS__COZYSTACK__DEFAULT_DOCTYPE", raising=False)
    backend = CozyStackLRSBackend()
    assert backend.settings.DEFAULT_DOCTYPE == "io.cozy.learningrecords"

    monkeypatch.setenv(
        "RALPH_BACKENDS__LRS__COZYSTACK__DEFAULT_DOCTYPE", "io.test.doctype"
    )
    backend = CozyStackLRSBackend()
    assert backend.settings.DEFAULT_DOCTYPE == "io.test.doctype"


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "selector": {},
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "selector": {"source.id": "statementId"},
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "selector": {
                    "source.id": "statementId",
                    "source.actor.mbox": "mailto:foo@bar.baz",
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "selector": {
                    "source.id": "statementId",
                    "source.actor.mbox_sha1sum": (
                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                    ),
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "selector": {
                    "source.id": "statementId",
                    "source.actor.openid": "http://toby.openid.example.org/",
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 5. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "statementId",
                "agent": {
                    "account__home_page": "http://www.example.com",
                    "account__name": "13936749",
                },
            },
            {
                "selector": {
                    "source.id": "statementId",
                    "source.actor.account.name": "13936749",
                    "source.actor.account.homePage": "http://www.example.com",
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 6. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "selector": {
                    "source.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "source.object.id": "http://www.example.com/meetings/34534",
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 7. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "selector": {
                    "source.timestamp": {
                        "$gt": "2021-06-24T00:00:20.194929+00:00",
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    }
                },
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 8. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0"},
            {
                "selector": {},
                "limit": 0,
                "skip": None,
                "sort": [{"source.timestamp": "desc"}, {"source.id": "desc"}],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": "1686557542970|0",
            },
        ),
    ],
)
def test_backends_lrs_cozystack_query_statements_query(
    params, expected_query, monkeypatch
):
    """Test the `CozyStackLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected CozyStack query.
    """

    def mock_read(query, target, chunk_size):
        """Mock the `CozyStackLRSBackend.read` method."""
        assert query.model_dump() == expected_query
        query.next = True
        query.bookmark = "abc"
        return []

    backend = CozyStackLRSBackend()
    monkeypatch.setattr(backend, "read", mock_read)

    result = backend.query_statements(RalphStatementsQuery.model_construct(**params))
    assert not result.statements
    assert result.search_after == "abc"


def test_backends_lrs_cozystack_query_statements(cozystack_custom, cozy_auth_target):
    """Test the `CozyStackLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents_default = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
    ]
    assert backend.write(documents_default, target=cozy_auth_target) == 2

    # Check the expected search query results.
    result = backend.query_statements(
        RalphStatementsQuery.model_construct(statement_id="1", limit=10),
        target=cozy_auth_target,
    )
    assert result.statements == documents_default[1:]


def test_backends_lrs_cozystack_query_statements_with_search_query_failure(
    monkeypatch, caplog, cozystack_custom, cozy_auth_target
):
    """
    Test the `CozyStackLRSBackend.query_statements`, given a search query failure,
    should raise a `BackendException` and log the error.
    """

    def mock_read(**_):
        """Mock the CozyStack.read method."""
        raise BackendException("Query error")

    cozystack_custom()
    backend = CozyStackLRSBackend()
    monkeypatch.setattr(backend, "read", mock_read)

    msg = "Query error"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.query_statements(
                RalphStatementsQuery.model_construct(), target=cozy_auth_target
            )

    assert (
        "ralph.backends.lrs.cozystack",
        logging.ERROR,
        "Failed to read from CozyStack",
    ) in caplog.record_tuples


def test_backends_lrs_cozystack_query_statements_by_ids_with_search_query_failure(
    monkeypatch, caplog, cozystack_custom, cozy_auth_target
):
    """
    Test the `CozyStackLRSBackend.query_statements_by_ids` method,
    given a search query failure, should raise a `BackendException` and log the error.
    """

    def mock_find(*_):
        """Mock the CozyStackClient.find method."""
        raise ExpiredTokenError()

    cozystack_custom()
    backend = CozyStackLRSBackend()
    monkeypatch.setattr(backend.client, "find", mock_find)

    msg = r"Authentication token has expired"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            list(
                backend.query_statements_by_ids(RalphStatementsQuery.model_construct())
            )

    assert (
        "ralph.backends.lrs.cozystack",
        logging.ERROR,
        "Failed to read from CozyStack",
    ) in caplog.record_tuples

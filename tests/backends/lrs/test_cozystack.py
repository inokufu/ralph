"""Tests for Ralph CozyStack LRS backend."""

import logging
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import LogCaptureFixture, MonkeyPatch

from ralph.backends.cozystack import CozyStackClient
from ralph.backends.cozystack.exceptions import ExpiredTokenError
from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.backends.lrs.cozystack import CozyStackLRSBackend
from ralph.exceptions import BackendException, BackendParameterException
from ralph.models.xapi.base.statements import VOIDED_VERB_ID


def test_backends_lrs_cozystack_default_instantiation(
    monkeypatch: MonkeyPatch, fs: FakeFilesystem
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
                "selector": {
                    "source.metadata.voided": False,
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "selector": {
                    "source.statement.id": "statementId",
                    "source.metadata.voided": False,
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
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
                    "source.statement.id": "statementId",
                    "source.metadata.voided": False,
                    "source.statement.actor.mbox": "mailto:foo@bar.baz",
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
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
                    "source.statement.id": "statementId",
                    "source.metadata.voided": False,
                    "source.statement.actor.mbox_sha1sum": (
                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                    ),
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
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
                    "source.statement.id": "statementId",
                    "source.metadata.voided": False,
                    "source.statement.actor.openid": "http://toby.openid.example.org/",
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
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
                    "source.statement.id": "statementId",
                    "source.metadata.voided": False,
                    "source.statement.actor.account.name": "13936749",
                    "source.statement.actor.account.homePage": "http://www.example.com",
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 6. Query by voidedStatementId.
        (
            {"voidedStatementId": "statementId"},
            {
                "selector": {
                    "source.statement.id": "statementId",
                    "source.metadata.voided": True,
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 7. Query by voidedStatementId, verb and activity
        (
            {
                "voidedStatementId": "statementId",
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "selector": {
                    "source.statement.id": "statementId",
                    "source.metadata.voided": True,
                    "source.statement.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "source.statement.object.id": "http://www.example.com/meetings/34534",
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 8. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "selector": {
                    "source.metadata.voided": False,
                    "source.statement.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "source.statement.object.id": "http://www.example.com/meetings/34534",
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 9. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "selector": {
                    "source.metadata.voided": False,
                    "source.statement.timestamp": {
                        "$gt": "2021-06-24T00:00:20.194929+00:00",
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    },
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": None,
            },
        ),
        # 10. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0"},
            {
                "selector": {
                    "source.metadata.voided": False,
                },
                "limit": 0,
                "skip": None,
                "sort": [
                    {"source.statement.timestamp": "desc"},
                    {"source.statement.id": "desc"},
                ],
                "fields": ["_id", "source"],
                "next": None,
                "bookmark": "1686557542970|0",
            },
        ),
    ],
)
def test_backends_lrs_cozystack_query_statements_query(
    params: dict[str, Any], expected_query: dict[str, Any], monkeypatch: MonkeyPatch
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


def test_backends_lrs_cozystack_query_statements(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents_default = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
    ]
    assert (
        backend.write(documents_default, {"voided": False}, target=cozy_auth_target)
        == 2
    )

    # Check the expected search query results.
    result = backend.query_statements(
        RalphStatementsQuery.model_construct(statement_id="1", limit=10),
        target=cozy_auth_target,
    )
    assert result.statements == documents_default[1:]

    result = backend.query_statements(
        RalphStatementsQuery.model_construct(voided_statement_id="1", limit=10),
        target=cozy_auth_target,
    )
    assert len(result.statements) == 0


def test_backends_lrs_cozystack_query_statements_voided(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.query_statements` method, given a query,
    should return matching voided statements.
    """
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents_default = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
    ]
    assert (
        backend.write(documents_default, {"voided": True}, target=cozy_auth_target) == 2
    )

    # Check the expected search query results.
    result = backend.query_statements(
        RalphStatementsQuery.model_construct(voided_statement_id="0", limit=10),
        target=cozy_auth_target,
    )
    assert result.statements == documents_default[:1]

    result = backend.query_statements(
        RalphStatementsQuery.model_construct(statement_id="0", limit=10),
        target=cozy_auth_target,
    )
    assert len(result.statements) == 0


def test_backends_lrs_cozystack_query_statements_with_search_query_failure(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
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


def test_backends_lrs_cozystack_query_statements_by_ids(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.query_statements_by_ids` method."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
        {"id": "2", "timestamp": "2023-04-26T00:00:20.194929+00:00"},
        {"id": "3", "timestamp": "2023-03-27T00:00:20.194929+00:00"},
    ]

    assert backend.write(documents[:2], {"voided": False}, target=cozy_auth_target) == 2
    assert backend.write(documents[2:], {"voided": True}, target=cozy_auth_target) == 2

    result = backend.query_statements_by_ids(
        ids=["0", "2"],
        target=cozy_auth_target,
    )

    assert list(result) == [documents[0], documents[2]]


def test_backends_lrs_cozystack_query_statements_by_ids_include_extra(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """
    Test the `CozyStackLRSBackend.query_statements_by_ids` method with include_extra.
    """
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
        {"id": "2", "timestamp": "2023-04-26T00:00:20.194929+00:00"},
        {"id": "3", "timestamp": "2023-03-27T00:00:20.194929+00:00"},
    ]

    assert backend.write(documents[:2], {"voided": False}, target=cozy_auth_target) == 2
    assert backend.write(documents[2:], {"voided": True}, target=cozy_auth_target) == 2

    result = backend.query_statements_by_ids(
        ids=["0", "2"], target=cozy_auth_target, include_extra=True
    )

    item = next(result)

    assert "_rev" in item["statement"]
    item["statement"].pop("_rev")

    assert item["statement"] == documents[0]
    assert item["metadata"] == {"voided": False}

    item = next(result)

    assert "_rev" in item["statement"]
    item["statement"].pop("_rev")

    assert item["statement"] == documents[2]
    assert item["metadata"] == {"voided": True}

    with pytest.raises(StopIteration):
        next(result)


def test_backends_lrs_cozystack_query_statements_by_ids_with_search_query_failure(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
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
            list(backend.query_statements_by_ids(["abc"], target=cozy_auth_target))

    assert (
        "ralph.backends.lrs.cozystack",
        logging.ERROR,
        "Failed to read from CozyStack",
    ) in caplog.record_tuples


def test_backends_lrs_cozystack_index_statements(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.index_statements` method."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
        {"id": "2", "timestamp": "2023-04-26T00:00:20.194929+00:00"},
        {"id": "3", "timestamp": "2023-03-27T00:00:20.194929+00:00"},
    ]

    assert backend.index_statements(documents, target=cozy_auth_target) == 4

    result = backend.query_statements_by_ids(
        ids=["0", "1", "2", "3"], target=cozy_auth_target, include_extra=True
    )

    for document, item in zip(documents, result, strict=True):
        item["statement"].pop("_rev")
        assert item["statement"] == document
        assert item["metadata"] == {"voided": False}


def test_backends_lrs_cozystack_void_statements(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.void_statements` method."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    documents = [
        {
            "id": "0",
            "timestamp": "2023-06-24T00:00:20.194929+00:00",
            "verb": {"id": "abc"},
        },
        {
            "id": "1",
            "timestamp": "2023-05-25T00:00:20.194929+00:00",
            "verb": {"id": "abc"},
        },
        {
            "id": "2",
            "timestamp": "2023-04-26T00:00:20.194929+00:00",
            "verb": {"id": "abc"},
        },
        {
            "id": "3",
            "timestamp": "2023-03-27T00:00:20.194929+00:00",
            "verb": {"id": "abc"},
        },
    ]

    assert backend.index_statements(documents, target=cozy_auth_target) == 4

    assert (
        backend.void_statements(
            voided_statements_ids=["0", "2"], target=cozy_auth_target
        )
        == 2
    )

    result = list(
        backend.query_statements_by_ids(
            ids=["0", "1", "2", "3"], target=cozy_auth_target, include_extra=True
        )
    )

    assert result[0]["metadata"]["voided"]
    assert result[2]["metadata"]["voided"]

    assert not result[1]["metadata"]["voided"]
    assert not result[3]["metadata"]["voided"]


def test_backends_lrs_cozystack_void_statements_error(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.void_statements` method with error."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    # voided statement does not exist
    with pytest.raises(
        BackendParameterException,
        match=(
            "StatementRef '0' of voiding Statement "
            "references a Statement that does not exist"
        ),
    ):
        backend.void_statements(voided_statements_ids=["0"], target=cozy_auth_target)

    # voided statement is a voiding statement
    assert (
        backend.index_statements(
            [
                {
                    "id": "0",
                    "timestamp": "2023-06-24T00:00:20.194929+00:00",
                    "verb": {"id": VOIDED_VERB_ID},
                }
            ],
            target=cozy_auth_target,
        )
        == 1
    )

    with pytest.raises(
        BackendParameterException,
        match=(
            "StatementRef '0' of voiding Statement "
            "references another voiding Statement"
        ),
    ):
        backend.void_statements(voided_statements_ids=["0"], target=cozy_auth_target)

    # voided statement has already been voided
    assert (
        backend.index_statements(
            [
                {
                    "id": "1",
                    "timestamp": "2023-06-25T00:00:20.194929+00:00",
                    "verb": {"id": "abc"},
                }
            ],
            target=cozy_auth_target,
        )
        == 1
    )

    backend.void_statements(voided_statements_ids=["1"], target=cozy_auth_target)

    with pytest.raises(
        BackendParameterException,
        match=(
            "StatementRef '1' of voiding Statement "
            "references a Statement that has already been voided"
        ),
    ):
        backend.void_statements(voided_statements_ids=["1"], target=cozy_auth_target)


def test_backends_lrs_cozystack_query_statements_bad_args(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.query_statements` method with bad args."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    for params in [0, "abc", {"a": "b"}, [1, 2, 3], True]:
        with pytest.raises(ValidationError):
            next(
                backend.query_statements(
                    params=params,
                    target=cozy_auth_target,
                )
            )

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            next(
                backend.query_statements(
                    params=RalphStatementsQuery.model_construct(statement_id="1"),
                    target=target,
                )
            )


def test_backends_lrs_cozystack_query_statements_by_ids_bad_args(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.query_statements_by_ids` method with bad args."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    for ids in [[0], 0, "0", "abc", True]:
        with pytest.raises(ValidationError):
            next(
                backend.query_statements_by_ids(
                    ids=ids,
                    target=cozy_auth_target,
                )
            )

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            next(
                backend.query_statements_by_ids(
                    ids=["0"],
                    target=target,
                )
            )

    for include_extra in [0, "abc", [True]]:
        with pytest.raises(ValidationError):
            next(
                backend.query_statements_by_ids(
                    ids=["0"], target=cozy_auth_target, include_extra=include_extra
                )
            )


def test_backends_lrs_cozystack_index_statements_bad_args(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.index_statemennts` method with bad args."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    for statements in [0, "abc", [0, 1, 2], ["a", "b", "c"], {"a": "b"}]:
        with pytest.raises(ValidationError):
            backend.index_statements(statements=statements)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            backend.index_statements(statements=[{"a": "b"}], target=target)


def test_backends_lrs_cozystack_void_statements_bad_args(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackLRSBackend.void_statemennts` method with bad args."""
    cozystack_custom()
    backend = CozyStackLRSBackend()

    for voided_statements_ids in [0, "abc", [0, 1, 2], {"a": "b"}]:
        with pytest.raises(ValidationError):
            backend.void_statements(voided_statements_ids=voided_statements_ids)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            backend.void_statements(
                voided_statements_ids=["a", "b", "c"], target=target
            )

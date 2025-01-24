"""Tests for Ralph CozyStack data backend."""

import json
import logging
from collections.abc import Callable
from io import BytesIO

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import LogCaptureFixture, MonkeyPatch

from ralph.backends.cozystack import (
    CozyStackClient,
    CozyStackError,
    DatabaseDoesNotExistError,
    ExpiredTokenError,
    ForbiddenError,
)
from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.cozystack import (
    CozyStackDataBackend,
    CozyStackDataBackendSettings,
    CozyStackQuery,
)
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now


def test_backends_data_cozystack_default_instantiation(
    monkeypatch: MonkeyPatch, fs: FakeFilesystem
):
    """Test the `CozyStackDataBackend` default instantiation."""

    fs.create_file(".env")

    backend_settings_names = ["DEFAULT_DOCTYPE"]

    for name in backend_settings_names:
        monkeypatch.delenv(f"RALPH_BACKENDS__DATA__COZYSTACK__{name}", raising=False)

    assert CozyStackDataBackend.name == "cozy-stack"
    assert CozyStackDataBackend.query_class == CozyStackQuery
    assert CozyStackDataBackend.default_operation_type == BaseOperationType.INDEX

    backend = CozyStackDataBackend()

    assert backend.settings.DEFAULT_DOCTYPE == "io.cozy.learningrecords"
    assert isinstance(backend.client, CozyStackClient)

    # Test overriding default values with environment variables.
    monkeypatch.setenv(
        "RALPH_BACKENDS__DATA__COZYSTACK__DEFAULT_DOCTYPE",
        "io.cozy.abc",
    )

    backend = CozyStackDataBackend()
    assert backend.settings.DEFAULT_DOCTYPE == "io.cozy.abc"


def test_backends_data_cozystack_instantiation_with_settings():
    """Test the `CozyStackDataBackend` instantiation with settings."""
    settings = CozyStackDataBackendSettings(DEFAULT_DOCTYPE="io.cozy.abc")
    backend = CozyStackDataBackend(settings)
    assert backend.settings.DEFAULT_DOCTYPE == "io.cozy.abc"
    assert isinstance(backend.client, CozyStackClient)
    backend.close()


@pytest.mark.parametrize(
    "exception_class",
    [
        ForbiddenError,
        ExpiredTokenError,
    ],
)
def test_backends_data_cozystack_list_with_failure(
    caplog: LogCaptureFixture,
    monkeypatch: MonkeyPatch,
    exception_class: type[Exception],
):
    """
    Test the `CozyStackDataBackend.list` method
    should raise a `BackendException` and log an error message.
    """

    def mock_list_all_doctypes(target):
        raise exception_class()

    backend = CozyStackDataBackend()

    monkeypatch.setattr(backend.client, "list_all_doctypes", mock_list_all_doctypes)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            next(backend.list())

    assert (
        "ralph.backends.data.cozystack",
        logging.ERROR,
        f"Failed to list CozyStack doctypes: {exception_class.message}",
    ) in caplog.record_tuples


def test_backends_data_cozystack_list_with_ignored_args(
    caplog: LogCaptureFixture,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
):
    """
    Test the `CozyStackDataBackend.list` method given `details` and `new` argument
    set to True, should log a warning message.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    with caplog.at_level(logging.WARNING):
        list(backend.list(cozy_auth_target, details=True, new=True))

    assert (
        "ralph.backends.data.cozystack",
        logging.WARNING,
        "The `details` argument is ignored",
    ) in caplog.record_tuples

    assert (
        "ralph.backends.data.cozystack",
        logging.WARNING,
        "The `new` argument is ignored",
    ) in caplog.record_tuples


def test_backends_data_cozystack_list(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    cozystack_custom()
    backend = CozyStackDataBackend()
    assert "io.cozy.learningrecords" in list(backend.list(cozy_auth_target))


@pytest.mark.parametrize(
    "exception_class",
    [
        ExpiredTokenError,
        ForbiddenError,
        DatabaseDoesNotExistError,
    ],
)
def test_backends_data_cozystack_read_with_failure(
    caplog: LogCaptureFixture,
    monkeypatch: MonkeyPatch,
    exception_class: type[Exception],
    cozy_auth_target: str,
):
    """
    Test the `CozyStackDataBackend.read` method, given a request failure,
    should raise a `BackendException`.
    """

    def mock_find(target, query):
        raise exception_class()

    backend = CozyStackDataBackend()

    monkeypatch.setattr(backend.client, "find", mock_find)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            next(backend.read(target=cozy_auth_target))

    assert (
        "ralph.backends.data.cozystack",
        logging.ERROR,
        f"Failed to execute CozyStack query: {exception_class.message}",
    ) in caplog.record_tuples


def test_backends_data_cozystack_read_with_ignored_args(
    caplog: LogCaptureFixture,
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
):
    """
    Test the `CozyStackDataBackend.read` method given `ignore_errors`
    argument set should log a warning message.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    with caplog.at_level(logging.WARNING):
        list(
            backend.read(
                query=CozyStackQuery(limit=1),
                target=cozy_auth_target,
                ignore_errors=True,
            )
        )

    assert (
        "ralph.backends.data.cozystack",
        logging.WARNING,
        "The `ignore_errors` argument is ignored",
    ) in caplog.record_tuples


def test_backends_data_cozystack_read_with_raw_ouput(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackDataBackend.read` method with `raw_output` set to `True`."""
    cozystack_custom()
    backend = CozyStackDataBackend()

    documents = [{"id": str(idx), "timestamp": now()} for idx in range(10)]
    assert backend.write(documents, target=cozy_auth_target) == 10

    hits = list(backend.read(target=cozy_auth_target, raw_output=True))

    for i, hit in enumerate(hits):
        assert isinstance(hit, bytes)
        assert json.loads(hit).get("source") == documents[i]


def test_backends_data_cozystack_read_without_raw_ouput(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test the `CozyStackDataBackend.read` method with `raw_output` set to `False`."""
    cozystack_custom()
    backend = CozyStackDataBackend()

    documents = [{"id": str(idx), "timestamp": now()} for idx in range(10)]
    assert backend.write(documents, target=cozy_auth_target) == 10

    hits = backend.read(target=cozy_auth_target)
    for i, hit in enumerate(hits):
        assert isinstance(hit, dict)
        assert hit.get("source") == documents[i]


def test_backends_data_cozystack_read_with_query(
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
    caplog: LogCaptureFixture,
):
    """Test the `CozyStackDataBackend.read` method with a query."""
    cozystack_custom()
    backend = CozyStackDataBackend()

    documents = [
        {"id": str(idx), "timestamp": now(), "modulo": idx % 2} for idx in range(5)
    ]
    assert backend.write(documents, target=cozy_auth_target) == 5

    # Find every even item.
    query = CozyStackQuery(selector={"source.modulo": 0})
    results = list(backend.read(query=query, target=cozy_auth_target))

    assert len(results) == 3
    assert results[0]["source"]["id"] == "0"
    assert results[1]["source"]["id"] == "2"
    assert results[2]["source"]["id"] == "4"

    # Find the first two even items.
    query = CozyStackQuery(selector={"source.modulo": 0}, limit=2)
    results = list(backend.read(query=query, target=cozy_auth_target))

    assert len(results) == 2
    assert results[0]["source"]["id"] == "0"
    assert results[1]["source"]["id"] == "2"

    # Find the first ten even items although there are only three available.
    query = CozyStackQuery(selector={"source.modulo": 0}, limit=10)
    results = list(backend.read(query=query, target=cozy_auth_target))

    assert len(results) == 3
    assert results[0]["source"]["id"] == "0"
    assert results[1]["source"]["id"] == "2"
    assert results[2]["source"]["id"] == "4"

    # Find every odd item.
    query = CozyStackQuery(selector={"source.modulo": 1})
    results = list(backend.read(query=query, target=cozy_auth_target))

    assert len(results) == 2
    assert results[0]["source"]["id"] == "1"
    assert results[1]["source"]["id"] == "3"

    # Find every odd item with a json query string.
    query = CozyStackQuery.from_string(json.dumps({"selector": {"source.modulo": 1}}))
    results = list(backend.read(query=query, target=cozy_auth_target))

    assert len(results) == 2
    assert results[0]["source"]["id"] == "1"
    assert results[1]["source"]["id"] == "3"

    # Check query argument type
    with pytest.raises(
        BackendParameterException,
        match="'query' argument is expected to be a CozyStackQuery instance",
    ):
        with caplog.at_level(logging.ERROR):
            list(backend.read(query={"not_query": "foo"}))

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        "The 'query' argument is expected to be a CozyStackQuery instance",
    ) in caplog.record_tuples


def test_backends_data_cozystack_write_with_create_operation(
    cozystack_custom: Callable[[], CozyStackClient],
    cozy_auth_target: str,
    caplog: LogCaptureFixture,
):
    """Test the `CozyStackDataBackend.write` method, given an `CREATE` `operation_type`,
    should insert the target documents with the provided data.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    assert len(list(backend.read(target=cozy_auth_target))) == 0

    # Given an empty data iterator, the write method should return 0 and log a message.
    data = []

    with caplog.at_level(logging.INFO):
        assert (
            backend.write(
                data, target=cozy_auth_target, operation_type=BaseOperationType.CREATE
            )
            == 0
        )

    assert (
        "ralph.backends.data.base",
        logging.INFO,
        "Data Iterator is empty; skipping write to target",
    ) in caplog.record_tuples

    data = ({"value": str(idx)} for idx in range(9))
    with caplog.at_level(logging.DEBUG):
        assert (
            backend.write(
                data,
                target=cozy_auth_target,
                operation_type=BaseOperationType.CREATE,
            )
            == 9
        )

    assert (
        "ralph.backends.data.cozystack",
        logging.INFO,
        "Finished writing 9 documents with success",
    ) in caplog.record_tuples

    hits = list(backend.read(target=cozy_auth_target))
    assert [hit["source"] for hit in hits] == [{"value": str(idx)} for idx in range(9)]


def test_backends_data_cozystack_write_with_delete_operation(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """
    Test the `CozyStackDataBackend.write` method, given a `DELETE` `operation_type`,
    should remove the target documents.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    data = [{"id": str(idx), "value": str(idx)} for idx in range(10)]

    assert len(list(backend.read(target=cozy_auth_target))) == 0
    assert backend.write(data, target=cozy_auth_target) == 10

    results = list(backend.read(target=cozy_auth_target))
    assert len(results) == 10

    data = [{"id": item["_id"], "_rev": item["_rev"]} for item in results[:3]]

    assert (
        backend.write(
            data, target=cozy_auth_target, operation_type=BaseOperationType.DELETE
        )
        == 3
    )

    hits = list(backend.read(target=cozy_auth_target))
    assert len(hits) == 7
    assert sorted([hit["source"]["id"] for hit in hits]) == [
        str(x) for x in range(3, 10)
    ]


def test_backends_data_cozystack_write_with_update_operation(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """
    Test the `CozyStackDataBackend.write` method, given an `UPDATE` `operation_type`,
    should overwrite the target documents with the provided data.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    data = BytesIO(
        "\n".join(
            [json.dumps({"id": str(idx), "value": str(idx)}) for idx in range(10)]
        ).encode("utf8")
    )

    assert len(list(backend.read(target=cozy_auth_target))) == 0
    assert backend.write(data, target=cozy_auth_target) == 10

    hits = list(backend.read(target=cozy_auth_target))
    assert len(hits) == 10
    assert sorted([hit["source"]["id"] for hit in hits]) == [str(x) for x in range(10)]
    assert sorted([hit["source"]["value"] for hit in hits]) == list(map(str, range(10)))

    data = BytesIO(
        "\n".join(
            [
                json.dumps(
                    {"id": hit["_id"], "_rev": hit["_rev"], "value": str(10 + idx)}
                )
                for idx, hit in enumerate(hits)
            ]
        ).encode("utf8")
    )

    assert (
        backend.write(
            data, target=cozy_auth_target, operation_type=BaseOperationType.UPDATE
        )
        == 10
    )

    hits = list(backend.read(target=cozy_auth_target))
    assert len(hits) == 10
    assert sorted([hit["source"]["id"] for hit in hits]) == [str(x) for x in range(10)]
    assert sorted([hit["source"]["value"] for hit in hits]) == [
        str(x + 10) for x in range(10)
    ]


def test_backends_data_cozystack_write_with_append_operation(
    cozystack_custom: Callable[[], CozyStackClient], caplog: LogCaptureFixture
):
    """Test the `CozyStackDataBackend.write` method, given an `APPEND` `operation_type`,
    should raise a `BackendParameterException`.
    """
    cozystack_custom()
    backend = CozyStackDataBackend()

    msg = "Append operation_type is not allowed"
    with pytest.raises(BackendParameterException, match=msg):
        with caplog.at_level(logging.ERROR):
            backend.write(data=[{}], operation_type=BaseOperationType.APPEND)

    assert (
        "ralph.backends.data.base",
        logging.ERROR,
        "Append operation_type is not allowed",
    ) in caplog.record_tuples


@pytest.mark.parametrize(
    "exception_class",
    [
        ValueError,
        CozyStackError,
    ],
)
def test_backends_data_cozystack_write_with_failure(
    caplog: LogCaptureFixture,
    monkeypatch: MonkeyPatch,
    exception_class: type[Exception],
    cozy_auth_target: str,
):
    """
    Test the `CozyStackDataBackend.write` method, given a request failure,
    should raise a `BackendException`.
    """

    def mock_bulk_operation(target, data, operation_type):
        raise exception_class("abc")

    backend = CozyStackDataBackend()

    monkeypatch.setattr(backend.client, "bulk_operation", mock_bulk_operation)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException):
            backend.write(
                data=[{}],
                target=cozy_auth_target,
                operation_type=BaseOperationType.CREATE,
            )

    assert (
        "ralph.backends.data.cozystack",
        logging.ERROR,
        "Failed to insert data: abc",
    ) in caplog.record_tuples

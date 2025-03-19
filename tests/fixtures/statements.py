"""Test fixtures for statements."""

from collections.abc import Callable

import pytest
from elasticsearch.helpers import bulk

from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.cozystack import CozyStackDataBackend
from ralph.backends.data.mongo import MongoDataBackend

from tests.fixtures.backends import (
    COZYSTACK_TEST_DOCTYPE,
    ES_TEST_INDEX,
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    get_async_es_test_backend,
    get_async_mongo_test_backend,
    get_cozystack_test_backend,
    get_es_test_backend,
    get_mongo_test_backend,
)

from ..helpers import configure_env_for_mock_cozy_auth


def insert_es_statements(es_client, statements, index=ES_TEST_INDEX):
    """Insert a bunch of example statements into Elasticsearch for testing."""
    bulk(
        es_client,
        [
            {
                "_index": index,
                "_id": statement["id"],
                "_op_type": "index",
                "_source": {"statement": statement, "metadata": {"voided": False}},
            }
            for statement in statements
        ],
    )
    es_client.indices.refresh()


def insert_mongo_statements(mongo_client, statements, collection):
    """Insert a bunch of example statements into MongoDB for testing."""
    database = getattr(mongo_client, MONGO_TEST_DATABASE)
    collection = getattr(database, collection)
    collection.insert_many(
        list(
            MongoDataBackend.to_documents(
                data=statements,
                metadata={"voided": False},
                ignore_errors=True,
                operation_type=BaseOperationType.CREATE,
            )
        )
    )


@pytest.fixture(params=["async_es", "async_mongo", "es", "mongo"])
def insert_statements_and_monkeypatch_backend(
    request, es_custom, mongo_custom, monkeypatch
):
    """(Security) Return a function that inserts statements into each backend."""

    def _insert_statements_and_monkeypatch_backend(statements, target=None):
        """Insert statements once into each backend."""
        backend_client_class_path = "ralph.api.routers.statements.BACKEND_CLIENT"
        if request.param == "async_es":
            target = target if target else ES_TEST_INDEX
            client = es_custom(index=target)
            insert_es_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_async_es_test_backend())
            return
        if request.param == "async_mongo":
            target = target if target else MONGO_TEST_COLLECTION
            client = mongo_custom(collection=target)
            insert_mongo_statements(client, statements, target)
            monkeypatch.setattr(
                backend_client_class_path, get_async_mongo_test_backend()
            )
            return
        if request.param == "es":
            target = target if target else ES_TEST_INDEX
            client = es_custom(index=target)
            insert_es_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_es_test_backend())
            return
        if request.param == "mongo":
            target = target if target else MONGO_TEST_COLLECTION
            client = mongo_custom(collection=target)
            insert_mongo_statements(client, statements, target)
            monkeypatch.setattr(backend_client_class_path, get_mongo_test_backend())
            return

    return _insert_statements_and_monkeypatch_backend


def insert_cozystack_statements(statements, target):
    settings = CozyStackDataBackend.settings_class(
        DEFAULT_DOCTYPE=COZYSTACK_TEST_DOCTYPE
    )
    backend = CozyStackDataBackend(settings=settings)

    success = backend.write(statements, {"voided": False}, target=target)
    assert success == len(statements)


@pytest.fixture
def init_cozystack_db_and_monkeypatch_backend(
    monkeypatch, cozystack_custom, cozy_auth_target
) -> Callable[[list[dict] | None], None]:
    """Return a function that inserts statements into CozyStack backend."""

    def _init_cozystack_db_and_monkeypatch_backend(statements=None):
        # set cozy as auth backend
        configure_env_for_mock_cozy_auth(monkeypatch)

        # set up a fresh database
        cozystack_custom()

        # insert statements if needed
        if statements is not None:
            insert_cozystack_statements(statements, cozy_auth_target)

        # set cozystack as data storage backend
        monkeypatch.setattr(
            "ralph.api.routers.statements.BACKEND_CLIENT", get_cozystack_test_backend()
        )

    return _init_cozystack_db_and_monkeypatch_backend

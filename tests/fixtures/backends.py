"""Test fixtures for backends."""

import asyncio
import os
from collections.abc import Generator, Mapping
from contextlib import asynccontextmanager
from functools import lru_cache
from multiprocessing import Process
from pathlib import Path
from typing import Callable

import pytest
import uvicorn
from elasticsearch import BadRequestError, Elasticsearch
from httpx import AsyncClient, ConnectError
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from ralph.backends import cozystack
from ralph.backends.data.async_es import AsyncESDataBackend
from ralph.backends.data.async_mongo import AsyncMongoDataBackend
from ralph.backends.data.es import ESDataBackend
from ralph.backends.data.fs import FSDataBackend
from ralph.backends.data.mongo import MongoDataBackend
from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.async_mongo import AsyncMongoLRSBackend
from ralph.backends.lrs.cozystack import CozyStackLRSBackend
from ralph.backends.lrs.es import ESLRSBackend
from ralph.backends.lrs.fs import FSLRSBackend
from ralph.backends.lrs.mongo import MongoLRSBackend
from ralph.conf import Settings, core_settings

# Elasticsearch backend defaults
ES_TEST_INDEX = os.environ.get("RALPH_BACKENDS__DATA__ES__TEST_INDEX", "test-index-foo")
ES_TEST_FORWARDING_INDEX = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_FORWARDING_INDEX", "test-index-foo-2"
)
ES_TEST_INDEX_TEMPLATE = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__INDEX_TEMPLATE", "test-index"
)
ES_TEST_INDEX_PATTERN = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_INDEX_PATTERN", "test-index-*"
)
ES_TEST_HOSTS = os.environ.get(
    "RALPH_BACKENDS__DATA__ES__TEST_HOSTS", "http://localhost:9200"
).split(",")

# Mongo backend defaults
MONGO_TEST_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_COLLECTION", "marsha"
)
MONGO_TEST_FORWARDING_COLLECTION = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_FORWARDING_COLLECTION", "marsha-2"
)
MONGO_TEST_DATABASE = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_DATABASE", "statements"
)
MONGO_TEST_CONNECTION_URI = os.environ.get(
    "RALPH_BACKENDS__DATA__MONGO__TEST_CONNECTION_URI", "mongodb://localhost:27017/"
)

# CozyStack backend defaults
COZYSTACK_TEST_DOCTYPE = os.environ.get(
    "RALPH_BACKENDS__DATA__COZYSTACK__TEST_DOCTYPE", "io.cozy.learningrecords"
)

RUNSERVER_TEST_HOST = os.environ.get("RALPH_RUNSERVER_TEST_HOST", "0.0.0.0")
RUNSERVER_TEST_PORT = int(os.environ.get("RALPH_RUNSERVER_TEST_PORT", 8101))


@lru_cache
def get_es_test_backend():
    """Return a ESLRSBackend backend instance using test defaults."""
    settings = ESLRSBackend.settings_class(
        HOSTS=ES_TEST_HOSTS, DEFAULT_INDEX=ES_TEST_INDEX
    )
    return ESLRSBackend(settings)


@lru_cache
def get_async_es_test_backend(index: str = ES_TEST_INDEX):
    """Return an AsyncESLRSBackend backend instance using test defaults."""
    settings = AsyncESLRSBackend.settings_class(
        ALLOW_YELLOW_STATUS=False,
        CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
        DEFAULT_INDEX=index,
        HOSTS=ES_TEST_HOSTS,
        LOCALE_ENCODING="utf8",
        POINT_IN_TIME_KEEP_ALIVE="1m",
        READ_CHUNK_SIZE=500,
        REFRESH_AFTER_WRITE="true",
        WRITE_CHUNK_SIZE=499,
    )
    return AsyncESLRSBackend(settings)


@lru_cache
def get_mongo_test_backend():
    """Return a MongoDatabase backend instance using test defaults."""
    settings = MongoLRSBackend.settings_class(
        CONNECTION_URI=MONGO_TEST_CONNECTION_URI,
        DEFAULT_DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=MONGO_TEST_COLLECTION,
    )
    return MongoLRSBackend(settings)


@lru_cache
def get_async_mongo_test_backend(
    connection_uri: str = MONGO_TEST_CONNECTION_URI,
    default_collection: str = MONGO_TEST_COLLECTION,
    client_options: Mapping | None = None,
):
    """Return an AsyncMongoDatabase backend instance using test defaults."""
    settings = AsyncMongoLRSBackend.settings_class(
        CONNECTION_URI=connection_uri,
        DEFAULT_DATABASE=MONGO_TEST_DATABASE,
        DEFAULT_COLLECTION=default_collection,
        CLIENT_OPTIONS=client_options if client_options else {},
        LOCALE_ENCODING="utf8",
        READ_CHUNK_SIZE=500,
        WRITE_CHUNK_SIZE=499,
    )
    return AsyncMongoLRSBackend(settings)


@lru_cache
def get_cozystack_test_backend():
    """Return a CozyStack backend instance using test defaults."""
    settings = CozyStackLRSBackend.settings_class(
        DEFAULT_DOCTYPE=COZYSTACK_TEST_DOCTYPE
    )
    return CozyStackLRSBackend(settings)


def get_es_fixture(host=ES_TEST_HOSTS, index=ES_TEST_INDEX):
    """Create / delete an Elasticsearch test index and yield an instantiated client."""
    client = Elasticsearch(host)
    try:
        client.indices.create(index=index)
    except BadRequestError:
        # The index might already exist
        client.indices.delete(index=index)
        client.indices.create(index=index)
    yield client
    client.indices.delete(index=index)


@pytest.fixture
def es():
    """Yield an Elasticsearch test client.

    See get_es_fixture above.
    """

    for es_client in get_es_fixture():
        yield es_client


@pytest.fixture
def es_forwarding():
    """Yield a second Elasticsearch test client.

    See get_es_fixture above.
    """
    for es_client in get_es_fixture(index=ES_TEST_FORWARDING_INDEX):
        yield es_client


@pytest.fixture
def es_custom():
    """Yield `_es_custom` function."""

    teardown = []
    client = Elasticsearch(ES_TEST_HOSTS)

    def _es_custom(host=ES_TEST_HOSTS, index=ES_TEST_INDEX):
        """Create the index and yield an Elasticsearch test client."""
        try:
            client.indices.create(index=index)
        except BadRequestError:
            # The index might already exist
            client.indices.delete(index=index)
            client.indices.create(index=index)
        teardown.append(index)
        return client

    yield _es_custom

    for index in teardown:
        client.indices.delete(index=index)
    client.close()


@pytest.fixture
def fs_backend(fs, settings_fs):
    """Return the `get_fs_data_backend` function."""

    fs.create_dir("foo")

    def get_fs_data_backend(path: str = "foo"):
        """Return an instance of `FSDataBackend`."""
        settings = FSDataBackend.settings_class(
            DEFAULT_DIRECTORY_PATH=path,
            DEFAULT_QUERY_STRING="*",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=1024,
            WRITE_CHUNK_SIZE=999,
        )
        return FSDataBackend(settings)

    return get_fs_data_backend


@pytest.fixture
def fs_lrs_backend(fs, settings_fs):
    """Return the `get_fs_data_backend` function."""

    fs.create_dir("foo")

    def get_fs_lrs_backend(path: str = "foo"):
        """Return an instance of FSLRSBackend."""
        settings = FSLRSBackend.settings_class(
            DEFAULT_DIRECTORY_PATH=Path(path),
            DEFAULT_QUERY_STRING="*",
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=1024,
            WRITE_CHUNK_SIZE=999,
        )
        return FSLRSBackend(settings)

    return get_fs_lrs_backend


@pytest.fixture(scope="session")
def anyio_backend():
    """Select asyncio backend for pytest anyio."""
    return "asyncio"


@pytest.fixture(params=["sync", "async"])
def flavor(request):
    """Parametrize fixture with `sync`/`async` flavor."""
    return request.param


@pytest.fixture
def async_mongo_backend():
    """Return the `get_mongo_data_backend` function."""

    def get_mongo_data_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: Mapping | None = None,
    ):
        """Return an instance of `MongoDataBackend`."""
        settings = AsyncMongoDataBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=499,
        )
        return AsyncMongoDataBackend(settings)

    return get_mongo_data_backend


@pytest.fixture
def async_mongo_lrs_backend():
    """Return the `get_async_mongo_test_backend` function."""

    get_async_mongo_test_backend.cache_clear()

    return get_async_mongo_test_backend


def get_mongo_fixture(
    connection_uri=MONGO_TEST_CONNECTION_URI,
    database=MONGO_TEST_DATABASE,
    collection=MONGO_TEST_COLLECTION,
):
    """Create / delete a Mongo test database + collection and yield an
    instantiated client.
    """
    client = MongoClient(connection_uri)
    database = getattr(client, database)
    try:
        database.create_collection(collection)
    except CollectionInvalid:
        # The collection might already exist
        database.drop_collection(collection)
        database.create_collection(collection)
    yield client
    database.drop_collection(collection)
    client.drop_database(database)


@pytest.fixture
def mongo():
    """Yield a Mongo test client.

    See get_mongo_fixture above.
    """
    for mongo_client in get_mongo_fixture():
        yield mongo_client


@pytest.fixture
def mongo_custom():
    """Yield `_mongo_custom` function."""

    teardown = []

    client = MongoClient(MONGO_TEST_CONNECTION_URI)
    database = getattr(client, MONGO_TEST_DATABASE)

    def _mongo_custom(collection=MONGO_TEST_COLLECTION):
        """Create the collection and yield the Mongo test client."""
        try:
            database.create_collection(collection)
        except CollectionInvalid:
            # The collection might already exist
            database.drop_collection(collection)
            database.create_collection(collection)
        teardown.append(collection)
        return client

    yield _mongo_custom

    for collection in teardown:
        database.drop_collection(collection)
    client.drop_database(database)
    client.close()


@pytest.fixture
def mongo_backend():
    """Return the `get_mongo_data_backend` function."""

    def get_mongo_data_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: Mapping | None = None,
    ):
        """Return an instance of `MongoDataBackend`."""
        settings = MongoDataBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=499,
        )
        return MongoDataBackend(settings)

    return get_mongo_data_backend


@pytest.fixture
def mongo_lrs_backend():
    """Return the `get_mongo_lrs_backend` function."""

    def get_mongo_lrs_backend(
        connection_uri: str = MONGO_TEST_CONNECTION_URI,
        default_collection: str = MONGO_TEST_COLLECTION,
        client_options: Mapping | None = None,
    ):
        """Return an instance of MongoLRSBackend."""
        settings = MongoLRSBackend.settings_class(
            CONNECTION_URI=connection_uri,
            DEFAULT_DATABASE=MONGO_TEST_DATABASE,
            DEFAULT_COLLECTION=default_collection,
            CLIENT_OPTIONS=client_options if client_options else {},
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            WRITE_CHUNK_SIZE=499,
        )
        return MongoLRSBackend(settings)

    return get_mongo_lrs_backend


@pytest.fixture
def mongo_forwarding():
    """Yield a second Mongo test client.

    See get_mongo_fixture above.
    """
    for mongo_client in get_mongo_fixture(collection=MONGO_TEST_FORWARDING_COLLECTION):
        yield mongo_client


@pytest.fixture
def cozystack_custom(
    cozy_auth_target,
) -> Generator[Callable[[], cozystack.CozyStackClient]]:
    """Yield `_cozystack_custom` function."""

    client = cozystack.CozyStackClient(doctype=COZYSTACK_TEST_DOCTYPE)

    def _cozystack_custom():
        """Create indices and yield client."""
        client.create_index(cozy_auth_target, [])
        client.create_index(cozy_auth_target, ["source.id"])
        client.create_index(cozy_auth_target, ["source.timestamp", "source.id"])

        return client

    yield _cozystack_custom

    try:
        client.delete_database(target=cozy_auth_target)
    except cozystack.DatabaseDoesNotExistError:
        pass


@pytest.fixture
def es_data_stream():
    """Create / delete an Elasticsearch test datastream and yield an instantiated
    client.
    """
    client = Elasticsearch(ES_TEST_HOSTS)
    # Create statements index template with enabled data stream
    index_patterns = [ES_TEST_INDEX_PATTERN]
    data_stream = {}
    template = {
        "mappings": {
            "dynamic": True,
            "dynamic_date_formats": [
                "strict_date_optional_time",
                "yyyy/MM/dd HH:mm:ss Z||yyyy/MM/dd Z",
            ],
            "dynamic_templates": [],
            "date_detection": True,
            "numeric_detection": True,
            # Note: We define an explicit mapping of the `timestamp` field to allow
            # the Elasticsearch database to be queried even if no document has
            # been inserted before.
            "properties": {
                "timestamp": {
                    "type": "date",
                    "index": True,
                }
            },
        },
        "settings": {
            "index": {
                "number_of_shards": "1",
                "number_of_replicas": "1",
            }
        },
    }
    client.indices.put_index_template(
        name=ES_TEST_INDEX_TEMPLATE,
        index_patterns=index_patterns,
        data_stream=data_stream,
        template=template,
    )

    # Create a datastream matching the index template
    client.indices.create_data_stream(name=ES_TEST_INDEX)

    yield client

    client.indices.delete_data_stream(name=ES_TEST_INDEX)
    client.indices.delete_index_template(name=ES_TEST_INDEX_TEMPLATE)


@pytest.fixture
def settings_fs(fs, monkeypatch):
    """Force Path instantiation with fake FS in ralph settings."""

    monkeypatch.setattr(
        "ralph.backends.data.mixins.settings",
        Settings(HISTORY_FILE=Path(core_settings.APP_DIR / "history.json")),
    )


@pytest.fixture
def async_es_backend():
    """Return the `get_async_es_data_backend` function."""

    def get_async_es_data_backend():
        """Return an instance of AsyncESDataBackend."""
        settings = AsyncESDataBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=ES_TEST_INDEX,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
        )
        return AsyncESDataBackend(settings)

    return get_async_es_data_backend


@pytest.fixture
def async_es_lrs_backend():
    """Return the `get_async_es_test_backend` function."""

    get_async_es_test_backend.cache_clear()

    return get_async_es_test_backend


@pytest.fixture
def es_backend():
    """Return the `get_es_data_backend` function."""

    def get_es_data_backend():
        """Return an instance of ESDataBackend."""
        settings = ESDataBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=ES_TEST_INDEX,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
        )
        return ESDataBackend(settings)

    return get_es_data_backend


@pytest.fixture
def es_lrs_backend():
    """Return the `get_es_lrs_backend` function."""

    def get_es_lrs_backend(index: str = ES_TEST_INDEX):
        """Return an instance of ESLRSBackend."""
        settings = ESLRSBackend.settings_class(
            ALLOW_YELLOW_STATUS=False,
            CLIENT_OPTIONS={"ca_certs": None, "verify_certs": None},
            DEFAULT_INDEX=index,
            HOSTS=ES_TEST_HOSTS,
            LOCALE_ENCODING="utf8",
            POINT_IN_TIME_KEEP_ALIVE="1m",
            READ_CHUNK_SIZE=500,
            REFRESH_AFTER_WRITE="true",
            WRITE_CHUNK_SIZE=499,
        )
        return ESLRSBackend(settings)

    return get_es_lrs_backend


@pytest.fixture
def events():
    """Return test events fixture."""
    return [{"id": idx} for idx in range(10)]


@pytest.fixture
def lrs():
    """Return a context manager that runs ralph's lrs server."""

    @asynccontextmanager
    async def runserver(app, host=RUNSERVER_TEST_HOST, port=RUNSERVER_TEST_PORT):
        process = Process(
            target=uvicorn.run,
            args=(app,),
            kwargs={"host": host, "port": port, "log_level": "debug"},
            daemon=True,
        )
        try:
            process.start()
            async with AsyncClient() as client:
                server_ready = False
                while not server_ready:
                    try:
                        response = await client.get(
                            f"http://{host}:{port}/whoami",
                            headers={"X-Experience-API-Version": "1.0.3"},
                        )
                        assert response.status_code == 401
                        server_ready = True
                    except ConnectError:
                        await asyncio.sleep(0.1)
            yield process
        finally:
            process.terminate()

    return runserver

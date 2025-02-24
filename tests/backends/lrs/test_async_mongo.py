"""Tests for Ralph MongoDB LRS backend."""

import logging

import pytest
from bson.objectid import ObjectId
from pydantic import ValidationError
from pymongo import ASCENDING, DESCENDING

from ralph.backends.lrs.async_mongo import AsyncMongoLRSBackend
from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.exceptions import BackendException, BackendParameterException
from ralph.models.xapi.base.statements import VOIDED_VERB_ID

from tests.fixtures.backends import (
    MONGO_TEST_COLLECTION,
    MONGO_TEST_DATABASE,
    MONGO_TEST_FORWARDING_COLLECTION,
)


def test_backends_lrs_async_mongo_default_instantiation(monkeypatch, fs):
    """Test the `AsyncMongoLRSBackend` default instantiation."""
    fs.create_file(".env")
    monkeypatch.delenv("RALPH_BACKENDS__LRS__MONGO__DEFAULT_COLLECTION", raising=False)
    backend = AsyncMongoLRSBackend()
    assert backend.settings.DEFAULT_COLLECTION == "marsha"

    monkeypatch.setenv("RALPH_BACKENDS__LRS__MONGO__DEFAULT_COLLECTION", "foo")
    backend = AsyncMongoLRSBackend()
    assert backend.settings.DEFAULT_COLLECTION == "foo"


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "filter": {
                    "_source.metadata.voided": False,
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": False,
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": False,
                    "_source.statement.actor.mbox": "mailto:foo@bar.baz",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": False,
                    "_source.statement.actor.mbox_sha1sum": (
                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                    ),
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": False,
                    "_source.statement.actor.openid": "http://toby.openid.example.org/",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 5. Query by statementId and agent with account IFI.
        (
            {
                "statementId": "statementId",
                "agent": {
                    "account__name": "13936749",
                    "account__home_page": "http://www.example.com",
                },
            },
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": False,
                    "_source.statement.actor.account.name": "13936749",
                    "_source.statement.actor.account.homePage": "http://www.example.com",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 6. Query by voidedStatementId.
        (
            {"voidedStatementId": "statementId"},
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": True,
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 7. Query by voidedStatementId and verb and activity.
        (
            {
                "voidedStatementId": "statementId",
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "filter": {
                    "_source.statement.id": "statementId",
                    "_source.metadata.voided": True,
                    "_source.statement.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "_source.statement.object.id": "http://www.example.com/meetings/34534",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 8. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "filter": {
                    "_source.metadata.voided": False,
                    "_source.statement.verb.id": "http://adlnet.gov/expapi/verbs/attended",
                    "_source.statement.object.id": "http://www.example.com/meetings/34534",
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 9. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "filter": {
                    "_source.metadata.voided": False,
                    "_source.statement.timestamp": {
                        "$gt": "2021-06-24T00:00:20.194929+00:00",
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    },
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 10. Query by timerange (with only until).
        (
            {
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "filter": {
                    "_source.metadata.voided": False,
                    "_source.statement.timestamp": {
                        "$lte": "2023-06-24T00:00:20.194929+00:00",
                    },
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 11. Query with pagination.
        (
            {"search_after": "666f6f2d6261722d71757578", "pit_id": None},
            {
                "filter": {
                    "_source.metadata.voided": False,
                    "_id": {"$lt": ObjectId("666f6f2d6261722d71757578")},
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", DESCENDING),
                    ("_id", DESCENDING),
                ],
            },
        ),
        # 12. Query with pagination in ascending order.
        (
            {"search_after": "666f6f2d6261722d71757578", "ascending": True},
            {
                "filter": {
                    "_source.metadata.voided": False,
                    "_id": {"$gt": ObjectId("666f6f2d6261722d71757578")},
                },
                "limit": 0,
                "projection": None,
                "sort": [
                    ("_source.statement.timestamp", ASCENDING),
                    ("_id", ASCENDING),
                ],
            },
        ),
    ],
)
@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_query(
    params, expected_query, async_mongo_lrs_backend, monkeypatch
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected MongoDB query.
    """

    async def mock_read(query, target, chunk_size):
        """Mock the `AsyncMongoLRSBackend.read` method."""
        assert query.model_dump() == expected_query
        assert chunk_size == expected_query.get("limit")
        yield {"_id": "search_after_id", "_source": {"statement": {}, "metadata": {}}}

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(**params)
    )
    assert result.statements == [{}]
    assert not result.pit_id
    assert result.search_after == "search_after_id"

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_with_success(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given a valid search
    query, should return the expected statements.
    """
    # Create a custom collection
    custom_target = "custom-target"
    getattr(mongo, MONGO_TEST_DATABASE).create_collection(custom_target)

    backend = async_mongo_lrs_backend()

    # Insert documents into default collection
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    meta = {
        "actor": {"account": {"name": "test_name", "homePage": "http://example.com"}},
        "verb": {"id": "verb_id"},
        "object": {"id": "http://example.com"},
    }
    documents = [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta},
        {"id": "62b9ce92fcde2b2edba56bf4", **timestamp, **meta},
    ]
    assert await backend.write(documents, {"voided": False}) == 2

    # Insert documents into the custom collection
    documents = [
        {"id": "12b9ce922c26b46b68ffc234", **timestamp, **meta},
        {"id": "22b9ce92fcde2b2edba56567", **timestamp, **meta},
    ]
    assert await backend.write(documents, {"voided": False}, target=custom_target) == 2

    statement_parameters = RalphStatementsQuery.model_construct(
        statement_id="62b9ce922c26b46b68ffc68f",
        agent={
            "account__name": "test_name",
            "account__home_page": "http://example.com",
        },
        verb="verb_id",
        activity="http://example.com",
        since="2020-01-01T00:00:00.000000+00:00",
        until="2022-12-01T15:36:50",
        search_after="62b9ce922c26b46b68ffc68f",
        ascending=True,
        limit=25,
    )
    statement_query_result = await backend.query_statements(statement_parameters)

    assert statement_query_result.statements == [
        {"id": "62b9ce922c26b46b68ffc68f", **timestamp, **meta}
    ]

    # Check that statements in the custom collection can also be queried
    statement_query_result = await backend.query_statements(
        RalphStatementsQuery.construct(), target=custom_target
    )

    assert statement_query_result.statements == [
        {"id": "12b9ce922c26b46b68ffc234", **timestamp, **meta},
        {"id": "22b9ce92fcde2b2edba56567", **timestamp, **meta},
    ]
    # Drop custom collection
    getattr(mongo, MONGO_TEST_DATABASE).drop_collection(custom_target)

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_voided(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given a query,
    should return matching voided statements.
    """
    backend = async_mongo_lrs_backend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
    ]
    assert await backend.write(documents, {"voided": True}) == 2

    # Check the expected search query results.
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(voided_statement_id="0", limit=10),
    )
    assert result.statements == documents[:1]

    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(statement_id="0", limit=10),
    )
    assert len(result.statements) == 0

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_with_query_failure(
    async_mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoLRSBackend.query_statements` method, given a search query
    failure, should raise a BackendException and log the error.
    """

    msg = "Failed to execute MongoDB query: Something is wrong"

    async def mock_read(**_):
        """Mock the `MongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {"statement": {}, "metadata": {}}}
        raise BackendException(msg)

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            await backend.query_statements(RalphStatementsQuery.model_construct())

    assert (
        "ralph.backends.lrs.async_mongo",
        logging.ERROR,
        "Failed to read from async MongoDB",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_by_ids_query_failure(
    async_mongo_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncMongoLRSBackend.query_statements_by_ids` method, given a search
    query failure, should raise a BackendException and log the error.
    """

    msg = "Failed to execute MongoDB query: Something is wrong"

    async def mock_read(**_):
        """Mock the `AsyncMongoDataBackend.read` method always raising an Exception."""
        yield {"_source": {"statement": {}, "metadata": {}}}
        raise BackendException(msg)

    backend = async_mongo_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BackendException, match=msg):
            _ = [
                statement
                async for statement in backend.query_statements_by_ids(["abc"])
            ]

    assert (
        "ralph.backends.lrs.async_mongo",
        logging.ERROR,
        "Failed to read from MongoDB",
    ) in caplog.record_tuples

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_by_ids_two_collections(
    mongo, mongo_forwarding, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.query_statements_by_ids` method, given a valid
    search query, should execute the query only on the specified collection and return
    the expected results.
    """

    # Instantiate Mongo Databases
    backend_1 = async_mongo_lrs_backend()
    backend_2 = async_mongo_lrs_backend(
        default_collection=MONGO_TEST_FORWARDING_COLLECTION
    )

    # Insert documents
    timestamp = {"timestamp": "2022-06-27T15:36:50"}
    assert await backend_1.write([{"id": "1", **timestamp}]) == 1
    assert await backend_2.write([{"id": "2", **timestamp}]) == 1

    # Check the expected search query results
    assert [
        statement async for statement in backend_1.query_statements_by_ids(["1"])
    ] == [{"id": "1", **timestamp}]
    assert not [
        statement async for statement in backend_1.query_statements_by_ids(["2"])
    ]
    assert not [
        statement async for statement in backend_2.query_statements_by_ids(["1"])
    ]
    assert [
        statement async for statement in backend_2.query_statements_by_ids(["2"])
    ] == [{"id": "2", **timestamp}]

    # Check that backends can also read from another target
    assert [
        statement
        async for statement in backend_1.query_statements_by_ids(
            ["2"], target=MONGO_TEST_FORWARDING_COLLECTION
        )
    ] == [{"id": "2", **timestamp}]
    assert [
        statement
        async for statement in backend_2.query_statements_by_ids(
            ["1"], target=MONGO_TEST_COLLECTION
        )
    ] == [{"id": "1", **timestamp}]

    backend_1.close()
    backend_2.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_by_ids_include_extra(
    mongo, async_mongo_lrs_backend
):
    """
    Test the `AsyncMongoLRSBackend.query_statements_by_ids` method with include_extra.
    """
    backend = async_mongo_lrs_backend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
        {"id": "2", "timestamp": "2023-04-26T00:00:20.194929+00:00"},
        {"id": "3", "timestamp": "2023-03-27T00:00:20.194929+00:00"},
    ]

    assert await backend.write(documents[:2], {"voided": False}) == 2
    assert await backend.write(documents[2:], {"voided": True}) == 2

    result = [
        x
        async for x in backend.query_statements_by_ids(
            ids=["0", "2"], include_extra=True
        )
    ]

    assert len(result) == 2

    assert result[0]["statement"] == documents[0]
    assert result[0]["metadata"] == {"voided": False}

    assert result[1]["statement"] == documents[2]
    assert result[1]["metadata"] == {"voided": True}

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_index_statements(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.index_statements` method."""
    backend = async_mongo_lrs_backend()

    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "1", "timestamp": "2023-05-25T00:00:20.194929+00:00"},
        {"id": "2", "timestamp": "2023-04-26T00:00:20.194929+00:00"},
        {"id": "3", "timestamp": "2023-03-27T00:00:20.194929+00:00"},
    ]

    assert await backend.index_statements(documents) == 4

    result = [
        x
        async for x in backend.query_statements_by_ids(
            ids=["0", "1", "2", "3"], include_extra=True
        )
    ]

    for document, item in zip(documents, result, strict=True):
        assert item["statement"] == document
        assert item["metadata"] == {"voided": False}

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_index_statements_error(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.index_statements` method with error."""
    backend = async_mongo_lrs_backend()

    # no id
    documents = [{"timestamp": "2023-06-24T00:00:20.194929+00:00"}]

    with pytest.raises(BackendException, match="has no 'id' field"):
        await backend.index_statements(documents)

    # no timestamp
    documents = [{"id": "0"}]

    with pytest.raises(BackendException, match="has no 'timestamp' field"):
        await backend.index_statements(documents)

    # Mongo ObjectId is made with id and timestamp but id alone is not unique
    documents = [
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
        {"id": "0", "timestamp": "2023-06-24T00:00:20.194929+00:00"},
    ]

    with pytest.raises(BackendException, match="Failed to insert document chunk"):
        await backend.index_statements(documents)

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_void_statements(mongo, async_mongo_lrs_backend):
    """Test the `AsyncMongoLRSBackend.void_statements` method."""
    backend = async_mongo_lrs_backend()

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

    assert await backend.index_statements(documents) == 4

    assert await backend.void_statements(voided_statements_ids=["0", "2"]) == 2

    result = [
        x
        async for x in backend.query_statements_by_ids(
            ids=["0", "1", "2", "3"], include_extra=True
        )
    ]

    assert result[0]["metadata"]["voided"]
    assert result[2]["metadata"]["voided"]

    assert not result[1]["metadata"]["voided"]
    assert not result[3]["metadata"]["voided"]

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_void_statements_error(
    mongo, async_mongo_lrs_backend
):
    """Test the `AsyncMongoLRSBackend.void_statements` method with error."""
    backend = async_mongo_lrs_backend()

    # voided statement does not exist
    with pytest.raises(
        BackendParameterException,
        match=(
            "StatementRef '0' of voiding Statement "
            "references a Statement that does not exist"
        ),
    ):
        await backend.void_statements(voided_statements_ids=["0"])

    # voided statement is a voiding statement
    assert (
        await backend.index_statements(
            [
                {
                    "id": "0",
                    "timestamp": "2023-06-24T00:00:20.194929+00:00",
                    "verb": {"id": VOIDED_VERB_ID},
                }
            ]
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
        await backend.void_statements(voided_statements_ids=["0"])

    # voided statement has already been voided
    assert (
        await backend.index_statements(
            [
                {
                    "id": "1",
                    "timestamp": "2023-06-25T00:00:20.194929+00:00",
                    "verb": {"id": "abc"},
                }
            ]
        )
        == 1
    )

    assert await backend.void_statements(voided_statements_ids=["1"]) == 1

    with pytest.raises(
        BackendParameterException,
        match=(
            "StatementRef '1' of voiding Statement "
            "references a Statement that has already been voided"
        ),
    ):
        await backend.void_statements(voided_statements_ids=["1"])

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_bad_args():
    """Test the `AsyncMongoLRSBackend.query_statements` method with bad args."""
    backend = AsyncMongoLRSBackend()

    for params in [0, "abc", {"a": "b"}, [1, 2, 3], True]:
        with pytest.raises(ValidationError):
            [x async for x in await backend.query_statements(params=params)]

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            [
                x
                async for x in await backend.query_statements(
                    params=RalphStatementsQuery.model_construct(statement_id="1"),
                    target=target,
                )
            ]

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_query_statements_by_ids_bad_args():
    """Test the `AsyncMongoLRSBackend.query_statements_by_ids` method with bad args."""
    backend = AsyncMongoLRSBackend()

    for ids in [[0], 0, "0", "abc", True]:
        with pytest.raises(ValidationError):
            [x async for x in backend.query_statements_by_ids(ids=ids)]

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            [
                x
                async for x in backend.query_statements_by_ids(
                    ids=["0"],
                    target=target,
                )
            ]

    for include_extra in [0, "abc", [True]]:
        with pytest.raises(ValidationError):
            [
                x
                async for x in backend.query_statements_by_ids(
                    ids=["0"], target="abc", include_extra=include_extra
                )
            ]

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_index_statements_bad_args():
    """Test the `AsyncMongoLRSBackend.index_statemennts` method with bad args."""
    backend = AsyncMongoLRSBackend()

    for statements in [0, "abc", [0, 1, 2], ["a", "b", "c"], {"a": "b"}]:
        with pytest.raises(ValidationError):
            await backend.index_statements(statements=statements)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            await backend.index_statements(statements=[{"a": "b"}], target=target)

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_mongo_void_statements_bad_args():
    """Test the `AsyncMongoLRSBackend.void_statemennts` method with bad args."""
    backend = AsyncMongoLRSBackend()

    for voided_statements_ids in [0, "abc", [0, 1, 2], {"a": "b"}]:
        with pytest.raises(ValidationError):
            await backend.void_statements(voided_statements_ids=voided_statements_ids)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            await backend.void_statements(
                voided_statements_ids=["a", "b", "c"], target=target
            )

    await backend.close()

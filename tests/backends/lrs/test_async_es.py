"""Tests for Ralph Elasticsearch LRS backend."""

import logging
import re

import pytest
from elastic_transport import ApiResponseMeta
from elasticsearch import ApiError
from elasticsearch.helpers import bulk
from pydantic import ValidationError

from ralph.backends.lrs.async_es import AsyncESLRSBackend
from ralph.backends.lrs.base import RalphStatementsQuery
from ralph.exceptions import BackendException, BackendParameterException
from ralph.models.xapi.base.statements import VOIDED_VERB_ID

from tests.fixtures.backends import ES_TEST_FORWARDING_INDEX, ES_TEST_INDEX


def test_backends_lrs_async_es_default_instantiation(monkeypatch, fs):
    """Test the `ESLRSBackend` default instantiation."""
    fs.create_file(".env")
    monkeypatch.delenv("RALPH_BACKENDS__LRS__ES__DEFAULT_INDEX", raising=False)
    backend = AsyncESLRSBackend()
    assert backend.settings.DEFAULT_INDEX == "statements"

    monkeypatch.setenv("RALPH_BACKENDS__LRS__ES__DEFAULT_INDEX", "foo")
    backend = AsyncESLRSBackend()
    assert backend.settings.DEFAULT_INDEX == "foo"


@pytest.mark.parametrize(
    "params,expected_query",
    [
        # 0. Default query.
        (
            {},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"metadata.voided": False}},
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 1. Query by statementId.
        (
            {"statementId": "statementId"},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": False}},
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 2. Query by statementId and agent with mbox IFI.
        (
            {"statementId": "statementId", "agent": {"mbox": "mailto:foo@bar.baz"}},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": False}},
                            {
                                "term": {
                                    "statement.actor.mbox.keyword": "mailto:foo@bar.baz"
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 3. Query by statementId and agent with mbox_sha1sum IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"mbox_sha1sum": "a7a5b7462b862c8c8767d43d43e865ffff754a64"},
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": False}},
                            {
                                "term": {
                                    "statement.actor.mbox_sha1sum.keyword": (
                                        "a7a5b7462b862c8c8767d43d43e865ffff754a64"
                                    )
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 4. Query by statementId and agent with openid IFI.
        (
            {
                "statementId": "statementId",
                "agent": {"openid": "http://toby.openid.example.org/"},
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": False}},
                            {
                                "term": {
                                    "statement.actor.openid.keyword": (
                                        "http://toby.openid.example.org/"
                                    )
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
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
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": False}},
                            {
                                "term": {
                                    "statement.actor.account.name.keyword": ("13936749")
                                }
                            },
                            {
                                "term": {
                                    "statement.actor.account.homePage.keyword": (
                                        "http://www.example.com"
                                    )
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 6. Query by voidedStatementId.
        (
            {"voidedStatementId": "statementId"},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": True}},
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
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
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"_id": "statementId"}},
                            {"term": {"metadata.voided": True}},
                            {
                                "term": {
                                    "statement.verb.id.keyword": (
                                        "http://adlnet.gov/expapi/verbs/attended"
                                    )
                                }
                            },
                            {
                                "term": {
                                    "statement.object.id.keyword": (
                                        "http://www.example.com/meetings/34534"
                                    )
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 8. Query by verb and activity.
        (
            {
                "verb": "http://adlnet.gov/expapi/verbs/attended",
                "activity": "http://www.example.com/meetings/34534",
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"metadata.voided": False}},
                            {
                                "term": {
                                    "statement.verb.id.keyword": (
                                        "http://adlnet.gov/expapi/verbs/attended"
                                    )
                                }
                            },
                            {
                                "term": {
                                    "statement.object.id.keyword": (
                                        "http://www.example.com/meetings/34534"
                                    )
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 9. Query by timerange (with since/until).
        (
            {
                "since": "2021-06-24T00:00:20.194929+00:00",
                "until": "2023-06-24T00:00:20.194929+00:00",
            },
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"metadata.voided": False}},
                            {
                                "range": {
                                    "statement.timestamp": {
                                        "gt": "2021-06-24T00:00:20.194929+00:00"
                                    }
                                }
                            },
                            {
                                "range": {
                                    "statement.timestamp": {
                                        "lte": "2023-06-24T00:00:20.194929+00:00"
                                    }
                                }
                            },
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 10. Query with pagination and pit_id.
        (
            {"search_after": "1686557542970|0", "pit_id": "46ToAwMDaWR5BXV1a"},
            {
                "pit": {"id": "46ToAwMDaWR5BXV1a", "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"metadata.voided": False}},
                        ]
                    }
                },
                "search_after": ["1686557542970", "0"],
                "size": 0,
                "sort": [{"statement.timestamp": {"order": "desc"}}],
                "track_total_hits": False,
            },
        ),
        # 11. Query ignoring statement sort order.
        (
            {"ignore_order": True},
            {
                "pit": {"id": None, "keep_alive": None},
                "q": None,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"metadata.voided": False}},
                        ]
                    }
                },
                "search_after": None,
                "size": 0,
                "sort": "_shard_doc",
                "track_total_hits": False,
            },
        ),
    ],
)
@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_query(
    params, expected_query, async_es_lrs_backend, monkeypatch
):
    """Test the `AsyncESLRSBackend.query_statements` method, given valid statement
    parameters, should produce the expected Elasticsearch query.
    """

    async def mock_read(query, target, chunk_size):
        """Mock the `AsyncESLRSBackend.read` method."""
        assert query.model_dump() == expected_query
        assert chunk_size == expected_query.get("size")
        query.pit.id = "foo_pit_id"
        query.search_after = ["bar_search_after", "baz_search_after"]
        yield {"_source": {"statement": {}, "metadata": {}}}

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(**params)
    )
    assert result.statements == [{}]
    assert result.pit_id == "foo_pit_id"
    assert result.search_after == "bar_search_after|baz_search_after"

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements(es_custom, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.query_statements` method, given a query,
    should return matching statements.
    """
    # Create a custom index
    custom_target = "custom-target"
    es_custom(index=custom_target)

    # Instantiate AsyncESLRSBackend.
    backend = async_es_lrs_backend()

    # Insert documents into default target.
    documents_default = [{"id": "2", "timestamp": "2023-06-24T00:00:20.194929+00:00"}]
    assert await backend.write(documents_default, {"voided": False}) == 1

    # Insert documents into custom target.
    documents_custom = [{"id": "3", "timestamp": "2023-05-25T00:00:20.194929+00:00"}]
    assert (
        await backend.write(documents_custom, {"voided": False}, target=custom_target)
        == 1
    )

    # Check the expected search query results.
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(limit=10)
    )
    assert result.statements == documents_default
    assert re.match(r"[0-9]+\|0", result.search_after)

    # Check the expected search query results on custom target.
    result = await backend.query_statements(
        RalphStatementsQuery.model_construct(limit=10), target=custom_target
    )
    assert result.statements == documents_custom
    assert re.match(r"[0-9]+\|0", result.search_after)

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_voided(es, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.query_statements` method, given a query,
    should return matching voided statements.
    """
    backend = async_es_lrs_backend()

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
async def test_backends_lrs_async_es_query_statements_pit_query_failure(
    es, async_es_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncESLRSBackend.query_statements` method, given a point in time
    query failure, should raise a `BackendException` and log the error.
    """

    async def mock_read(**_):
        """Mock the Elasticsearch.read method."""
        yield {"_source": {"statement": {}, "metadata": {}}}
        raise BackendException("Query error")

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend, "read", mock_read)

    msg = "Query error"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            await backend.query_statements(RalphStatementsQuery.model_construct())

    await backend.close()

    assert (
        "ralph.backends.lrs.async_es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_es_query_statements_by_ids_search_query_failure(
    es, async_es_lrs_backend, monkeypatch, caplog
):
    """Test the `AsyncESLRSBackend.query_statements_by_ids` method, given a search
    query failure, should raise a `BackendException` and log the error.
    """

    def mock_search(**_):
        """Mock the Elasticsearch.search method."""
        raise ApiError("Query error", ApiResponseMeta(*([None] * 5)), None)

    backend = async_es_lrs_backend()
    monkeypatch.setattr(backend.client, "search", mock_search)

    msg = r"Failed to execute Elasticsearch query: ApiError\(None, 'Query error'\)"
    with pytest.raises(BackendException, match=msg):
        with caplog.at_level(logging.ERROR):
            _ = [
                statement
                async for statement in backend.query_statements_by_ids(["abc"])
            ]

    await backend.close()

    assert (
        "ralph.backends.lrs.async_es",
        logging.ERROR,
        "Failed to read from Elasticsearch",
    ) in caplog.record_tuples


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_by_ids_many_indexes(
    es, es_forwarding, async_es_lrs_backend
):
    """Test the `AsyncESLRSBackend.query_statements_by_ids` method, given a valid
    search query, should execute the query uniquely on the specified index and return
    the expected results.
    """

    # Insert documents.
    index_1_document = {
        "_index": ES_TEST_INDEX,
        "_id": "1",
        "_source": {"statement": {"id": "1"}},
    }
    index_2_document = {
        "_index": ES_TEST_FORWARDING_INDEX,
        "_id": "2",
        "_source": {"statement": {"id": "2"}},
    }
    bulk(es, [index_1_document])
    bulk(es_forwarding, [index_2_document])

    # As we bulk insert documents, the index needs to be refreshed before making
    # queries.
    es.indices.refresh(index=ES_TEST_INDEX)
    es_forwarding.indices.refresh(index=ES_TEST_FORWARDING_INDEX)

    # Instantiate AsyncESLRSBackends.
    backend_1 = async_es_lrs_backend(index=ES_TEST_INDEX)
    backend_2 = async_es_lrs_backend(index=ES_TEST_FORWARDING_INDEX)

    # Check the expected search query results.
    index_1_document = {"id": "1"}
    index_2_document = {"id": "2"}
    assert [
        statement async for statement in backend_1.query_statements_by_ids(["1"])
    ] == [index_1_document]
    assert not [
        statement async for statement in backend_1.query_statements_by_ids(["2"])
    ]
    assert not [
        statement async for statement in backend_2.query_statements_by_ids(["1"])
    ]
    assert [
        statement async for statement in backend_2.query_statements_by_ids(["2"])
    ] == [index_2_document]

    # Check that backends can also read from another target
    assert [
        statement
        async for statement in backend_1.query_statements_by_ids(
            ["2"], target=ES_TEST_FORWARDING_INDEX
        )
    ] == [index_2_document]
    assert [
        statement
        async for statement in backend_2.query_statements_by_ids(
            ["1"], target=ES_TEST_INDEX
        )
    ] == [index_1_document]

    await backend_1.close()
    await backend_2.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_query_statements_by_ids_include_extra(
    es, async_es_lrs_backend
):
    """
    Test the `AsyncESLRSBackend.query_statements_by_ids` method with include_extra.
    """
    backend = async_es_lrs_backend()

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
async def test_backends_lrs_async_es_index_statements(es, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.index_statements` method."""
    backend = async_es_lrs_backend()

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
async def test_backends_lrs_async_es_void_statements(es, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.void_statements` method."""
    backend = async_es_lrs_backend()

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
            ids=["0", "2"], include_extra=True
        )
    ]

    for item in result:
        assert item["metadata"]["voided"]

    result = [
        x
        async for x in backend.query_statements_by_ids(
            ids=["1", "3"], include_extra=True
        )
    ]

    for item in result:
        assert not item["metadata"]["voided"]

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_void_statements_error(es, async_es_lrs_backend):
    """Test the `AsyncESLRSBackend.void_statements` method with error."""
    backend = async_es_lrs_backend()

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
async def test_backends_lrs_async_es_query_statements_bad_args():
    """Test the `AsyncESLRSBackend.query_statements` method with bad args."""
    backend = AsyncESLRSBackend()

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
async def test_backends_lrs_async_es_query_statements_by_ids_bad_args():
    """Test the `AsyncESLRSBackend.query_statements_by_ids` method with bad args."""
    backend = AsyncESLRSBackend()

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
async def test_backends_lrs_async_es_index_statements_bad_args():
    """Test the `AsyncESLRSBackend.index_statemennts` method with bad args."""
    backend = AsyncESLRSBackend()

    for statements in [0, "abc", [0, 1, 2], ["a", "b", "c"], {"a": "b"}]:
        with pytest.raises(ValidationError):
            await backend.index_statements(statements=statements)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            await backend.index_statements(statements=[{"a": "b"}], target=target)

    await backend.close()


@pytest.mark.anyio
async def test_backends_lrs_async_es_void_statements_bad_args():
    """Test the `AsyncESLRSBackend.void_statemennts` method with bad args."""
    backend = AsyncESLRSBackend()

    for voided_statements_ids in [0, "abc", [0, 1, 2], {"a": "b"}]:
        with pytest.raises(ValidationError):
            await backend.void_statements(voided_statements_ids=voided_statements_ids)

    for target in [0, [0], True]:
        with pytest.raises(ValidationError):
            await backend.void_statements(
                voided_statements_ids=["a", "b", "c"], target=target
            )

    await backend.close()

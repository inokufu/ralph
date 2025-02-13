"""Test for CozyStack client."""

from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException, status
from httpx import Request, Response
from pydantic import ValidationError

from ralph.backends.cozystack import (
    CozyStackClient,
    CozyStackError,
    DatabaseDoesNotExistError,
    ExecutionError,
    ExpiredTokenError,
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
)
from ralph.backends.data.base import BaseOperationType

from tests.fixtures.backends import COZYSTACK_TEST_DOCTYPE


@pytest.mark.anyio
async def test_cozystack_client_create_index(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test index creation."""
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.create_index(cozy_auth_target, fields=["abc"])
    assert response["result"] == "created"

    response = client.create_index(cozy_auth_target, fields=["abc"])
    assert response["result"] == "exists"

    for bad_value in [[123], "abc", True]:
        with pytest.raises(ValidationError):
            client.create_index(cozy_auth_target, fields=bad_value)


@pytest.mark.anyio
async def test_cozystack_client_delete_database(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test database deletion."""
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.delete_database(target=cozy_auth_target)
    assert response["deleted"]
    assert response["ok"]

    with pytest.raises(DatabaseDoesNotExistError):
        client.delete_database(target=cozy_auth_target)


@pytest.mark.anyio
async def test_cozystack_client_list_all_doctypes(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test doctype listing."""
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.list_all_doctypes(target=cozy_auth_target)
    assert "io.cozy.learningrecords" in response


@pytest.mark.anyio
async def test_cozystack_client_find(
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_target: str,
):
    """Test database querying with and without filter/selector."""
    statements = [
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "value": 0,
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "value": 1,
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    # find all w/o selector
    response = client.find(target=cozy_auth_target, query={"selector": {}})
    assert len(response["docs"]) == 2
    assert not response["next"]

    # find w/ selector
    response = client.find(
        target=cozy_auth_target, query={"selector": {"source.value": 0}}
    )
    assert len(response["docs"]) == 1
    assert not response["next"]
    assert response["docs"][0]["_id"] == statements[0]["id"]

    # test bookmark
    response = client.find(target=cozy_auth_target, query={"selector": {}, "limit": 1})
    assert len(response["docs"]) == 1
    assert response["next"]
    assert response["docs"][0]["_id"] == statements[0]["id"]

    response = client.find(
        target=cozy_auth_target,
        query={"selector": {}, "bookmark": response["bookmark"]},
    )
    assert len(response["docs"]) == 1
    assert not response["next"]
    assert response["docs"][0]["_id"] == statements[1]["id"]


@pytest.mark.anyio
async def test_cozystack_client_find_no_match(
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_target: str,
):
    """Test database querying with and without filter/selector."""
    statements = [
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "value": 0,
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "value": 1,
        },
    ]

    init_cozystack_db_and_monkeypatch_backend(statements)
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    # find w/ selector that does not match anything
    for query in [
        {"selector": {"source.value": "abc"}},
        {"selector": {"source.test": 0}},
    ]:
        response = client.find(target=cozy_auth_target, query=query)
        assert len(response["docs"]) == 0


@pytest.mark.anyio
async def test_cozystack_client_find_bad_query(
    init_cozystack_db_and_monkeypatch_backend: Callable[[list[dict] | None], None],
    cozy_auth_target: str,
):
    """Test database querying with and without filter/selector."""
    init_cozystack_db_and_monkeypatch_backend()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    # malformed query
    for query in [{"filter": {}}, {"selector": "abc"}, {"selector": {}, "limit": -1}]:
        with pytest.raises(InvalidRequestError):
            client.find(target=cozy_auth_target, query=query)

    # wrong type query
    for query in ["abc", 123, True]:
        with pytest.raises(ValidationError):
            client.find(target=cozy_auth_target, query=query)


@pytest.mark.anyio
async def test_cozystack_client_bulk_operation(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test index, update and delete operation."""
    statements = [
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "value": 0,
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "value": 1,
        },
    ]

    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    # index statements
    response = client.bulk_operation(
        target=cozy_auth_target, data=statements, operation_type=BaseOperationType.INDEX
    )
    assert response == len(statements)

    # try to index twice
    response = client.bulk_operation(
        target=cozy_auth_target, data=statements, operation_type=BaseOperationType.INDEX
    )
    assert response == 0

    # update statements
    response = client.find(target=cozy_auth_target, query={"selector": {}})

    updated_statements = [
        {
            "id": item["_id"],
            "_rev": item["_rev"],
            "timestamp": item["source"]["timestamp"],
            "value": item["source"]["value"] + 10,
        }
        for item in response["docs"]
    ]

    response = client.bulk_operation(
        target=cozy_auth_target,
        data=updated_statements,
        operation_type=BaseOperationType.UPDATE,
    )
    assert response == 2

    response = client.find(target=cozy_auth_target, query={"selector": {}})

    for idx in range(2):
        assert response["docs"][idx]["_id"] == statements[idx]["id"]
        assert (
            response["docs"][idx]["source"]["timestamp"] == statements[idx]["timestamp"]
        )
        assert response["docs"][idx]["source"]["value"] == statements[idx]["value"] + 10

    # delete statements
    deleted_statements = [
        {
            "id": response["docs"][1]["_id"],
            "_rev": response["docs"][1]["_rev"],
        }
    ]

    response = client.bulk_operation(
        target=cozy_auth_target,
        data=deleted_statements,
        operation_type=BaseOperationType.DELETE,
    )
    assert response == 1

    response = client.find(target=cozy_auth_target, query={"selector": {}})
    assert len(response["docs"]) == 1
    assert response["docs"][0]["_id"] == statements[0]["id"]


@pytest.mark.anyio
async def test_cozystack_client_bulk_operation_bad_param(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test index, update and delete operation."""
    statements = [
        {
            "id": "72c81e98-1763-4730-8cfc-f5ab34f1bad2",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "value": 0,
        },
        {
            "id": "be67b160-d958-4f51-b8b8-1892002dbac6",
            "timestamp": datetime.now().isoformat(),
            "value": 1,
        },
    ]

    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    # bad operation_type
    with pytest.raises(ValidationError):
        client.bulk_operation(
            target=cozy_auth_target, data=statements, operation_type="BAD_OPERATION"
        )

    # bad data
    for data in ["abc", 123, {"a": "b"}, ["abc", "def"], [123, 456], []]:
        with pytest.raises(ValidationError):
            client.bulk_operation(
                target=cozy_auth_target,
                data=data,
                operation_type=BaseOperationType.INDEX,
            )


@pytest.mark.anyio
async def test_cozystack_client_bad_doctype(
    cozystack_custom: Callable[[], CozyStackClient], cozy_auth_target: str
):
    """Test index creation and database deletion when wrong doctype is given."""
    cozystack_custom()
    client = CozyStackClient("io.cozy.baddoctype")

    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        client.create_index(cozy_auth_target, fields=["abc"])

    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        client.delete_database(cozy_auth_target)


@pytest.mark.anyio
async def test_cozystack_client_bad_target(
    cozystack_custom: Callable[[], CozyStackClient]
):
    """
    Test index creation, database deletion and doctype listing
    when wrong target is given.
    """
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    with pytest.raises(
        HTTPException, match="400: Can't validate Cozy authentication data"
    ):
        client.create_index(target="abc", fields=["abc"])

    with pytest.raises(
        HTTPException, match="400: Can't validate Cozy authentication data"
    ):
        client.delete_database(target="abc")

    with pytest.raises(
        HTTPException, match="400: Can't validate Cozy authentication data"
    ):
        client.list_all_doctypes(target="abc")


@pytest.mark.anyio
def test_check_error():
    request = Request("GET", "http://cozy.fr")

    for ok_status in [
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
        status.HTTP_204_NO_CONTENT,
    ]:
        CozyStackClient.check_error(
            response=Response(request=request, status_code=ok_status)
        )

    response = Response(
        request=request,
        json={"error": "code=400, message=Expired token"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    with pytest.raises(ExpiredTokenError):
        CozyStackClient.check_error(response=response)

    response = Response(
        request=request,
        json={"abc": "def"},
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    with pytest.raises(InvalidRequestError):
        CozyStackClient.check_error(response=response)

    response = Response(
        request=request,
        json={"abc": "def"},
        status_code=status.HTTP_403_FORBIDDEN,
    )

    with pytest.raises(ForbiddenError):
        CozyStackClient.check_error(response=response)

    response = Response(
        request=request,
        json={"abc": "def", "reason": "Database does not exist."},
        status_code=status.HTTP_404_NOT_FOUND,
    )

    with pytest.raises(DatabaseDoesNotExistError):
        CozyStackClient.check_error(response=response)

    response = Response(
        request=request,
        json={"abc": "def"},
        status_code=status.HTTP_404_NOT_FOUND,
    )

    with pytest.raises(NotFoundError):
        CozyStackClient.check_error(response=response)

    response = Response(
        request=request,
        json={"abc": "def"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    with pytest.raises(ExecutionError):
        CozyStackClient.check_error(response=response)

    for ko_status in [
        status.HTTP_405_METHOD_NOT_ALLOWED,
        status.HTTP_406_NOT_ACCEPTABLE,
        status.HTTP_502_BAD_GATEWAY,
    ]:
        response = Response(
            request=request,
            json={"abc": "def"},
            status_code=ko_status,
        )

        with pytest.raises(CozyStackError):
            CozyStackClient.check_error(response=response)

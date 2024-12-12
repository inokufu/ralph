"""Test for CozyStack client."""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException, status
from httpx import Request, Response

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
async def test_cozystack_client_create_index(cozystack_custom, cozy_auth_target):
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.create_index(cozy_auth_target, fields=["abc"])
    assert response["result"] == "created"

    response = client.create_index(cozy_auth_target, fields=["abc"])
    assert response["result"] == "exists"


@pytest.mark.anyio
async def test_cozystack_client_delete_database(cozystack_custom, cozy_auth_target):
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.delete_database(target=cozy_auth_target)
    assert response["deleted"]
    assert response["ok"]

    with pytest.raises(DatabaseDoesNotExistError):
        client.delete_database(target=cozy_auth_target)


@pytest.mark.anyio
async def test_cozystack_client_list_all_doctypes(cozystack_custom, cozy_auth_target):
    cozystack_custom()
    client = CozyStackClient(COZYSTACK_TEST_DOCTYPE)

    response = client.list_all_doctypes(target=cozy_auth_target)
    assert "io.cozy.learningrecords" in response


@pytest.mark.anyio
async def test_cozystack_client_find(
    init_cozystack_db_and_monkeypatch_backend, cozy_auth_target
):
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

    # bad query
    with pytest.raises(InvalidRequestError):
        client.find(target=cozy_auth_target, query={"filter": {}})


@pytest.mark.anyio
async def test_cozystack_client_bulk_operation(cozystack_custom, cozy_auth_target):
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
async def test_cozystack_client_bulk_operation_missing_rev(
    cozystack_custom, cozy_auth_target
):
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

    # update statements without _rev
    response = client.find(target=cozy_auth_target, query={"selector": {}})

    updated_statements = [
        {
            "id": item["_id"],
            "timestamp": item["source"]["timestamp"],
            "value": item["source"]["value"] + 10,
        }
        for item in response["docs"]
    ]

    with pytest.raises(
        ValueError, match="Missing `_rev` field in item for update or delete operation"
    ):
        client.bulk_operation(
            target=cozy_auth_target,
            data=updated_statements,
            operation_type=BaseOperationType.UPDATE,
        )

    # delete statements without _rev
    deleted_statements = [{"id": response["docs"][1]["_id"]}]

    with pytest.raises(
        ValueError, match="Missing `_rev` field in item for update or delete operation"
    ):
        client.bulk_operation(
            target=cozy_auth_target,
            data=deleted_statements,
            operation_type=BaseOperationType.DELETE,
        )


@pytest.mark.anyio
async def test_cozystack_client_bad_doctype(cozystack_custom, cozy_auth_target):
    cozystack_custom()
    client = CozyStackClient("io.cozy.baddoctype")

    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        client.create_index(cozy_auth_target, fields=["abc"])

    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        client.delete_database(cozy_auth_target)


@pytest.mark.anyio
async def test_cozystack_client_bad_target(cozystack_custom):
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

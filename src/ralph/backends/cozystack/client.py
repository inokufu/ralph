"""CozyStack client for Ralph."""

import os
from typing import Dict, Iterable, List, Optional

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from ralph.backends.cozystack.exceptions import check_cozystack_error
from ralph.backends.data.base import BaseOperationType
from ralph.models.cozy import CozyAuthData


class CozyStackHttpClient:
    """Wrapper of httpx.Client to request CozyStack."""

    def __init__(self, target: Optional[str]):
        """Instantiate the CozyStack client."""
        try:
            self.cozy_auth_data = CozyAuthData.model_validate_json(target)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can't validate Cozy authentication data",
            ) from exc

    def __enter__(self) -> httpx.Client:
        """Instanciate httpx.Client object."""
        base_url = os.path.join(str(self.cozy_auth_data.instance_url), "data")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.cozy_auth_data.token,
        }

        self.client = httpx.Client(base_url=base_url, headers=headers)

        return self.client

    def __exit__(self, *args):
        """Close httpx.Client connexion."""
        self.client.close()


class CozyStackClient:
    """CozyStack low-level client. Provides a straightforward mappingfrom Python to CozyStack REST APIs."""  # noqa: E501

    def __init__(self, doctype: str):
        """Instanciate the CozyStack client."""
        self.doctype = doctype

    def create_index(self, target: str, fields: List[str]) -> Dict:
        """Create an index for some documents.

        Return:
            Dict: Index creation informations.

        Raises:
            fastapi.HTTPException: When target is malformed.
            CozyStackError: see ralph.backends.cozystack.exceptions.
        """
        url = os.path.join("/", self.doctype, "_index")

        with CozyStackHttpClient(target=target) as client:
            response = client.post(url, json={"index": {"fields": fields}})
            check_cozystack_error(response)
            return response.json()

    def delete_database(self, target: str) -> Dict:
        """Delete doctype database.

        Attributes:
            target (str): The target instance url with auth data.

        Return:
            Dict: Database deletion informations.

        Raises:
            fastapi.HTTPException: When target is malformed.
            CozyStackError: see ralph.backends.cozystack.exceptions.
        """
        url = os.path.join("/", self.doctype, "")

        with CozyStackHttpClient(target=target) as client:
            response = client.delete(url)
            check_cozystack_error(response)
            return response.json()

    def list_all_doctypes(self, target: str) -> List[str]:
        """List all doctypes available on targeted instance.

        Attributes:
            target (str): The target instance url with auth data.

        Return:
            List[str]: The doctypes available on targeted instance.

        Raises:
            fastapi.HTTPException: When target is malformed.
            CozyStackError: see ralph.backends.cozystack.exceptions.
        """
        with CozyStackHttpClient(target=target) as client:
            response = client.get("/_all_doctypes")
            check_cozystack_error(response)
            return response.json()

    def find(self, target: str, query: Dict) -> Dict:
        """Find document using a mango selector.

        Attributes:
            target (str): The target instance url with auth data.
            query (CozyStackQuery): The query to select records to read.

        Return:
            Dict: Response containing records to read.

        Raises:
            fastapi.HTTPException: When target is malformed.
            CozyStackError: see ralph.backends.cozystack.exceptions.
        """
        url = os.path.join("/", self.doctype, "_find")

        with CozyStackHttpClient(target=target) as client:
            response = client.post(url, json=query)
            check_cozystack_error(response)
            return response.json()

    @classmethod
    def _check_item_for_update_or_delete_operation(cls, item: Dict):
        """Raise ValueError if _id or _rev field missing in item."""
        for field in ["_id", "_rev"]:
            if field not in item:
                raise ValueError(
                    f"Missing `{field}` field in item for update or delete operation"
                )

    @classmethod
    def _prepare_data(cls, data: Iterable[dict], operation_type: BaseOperationType):
        """Enrich data based on operation type."""
        prepared_data = []

        for item in data:
            prepared_item = {}

            if "id" in item:
                item["id"] = str(item["id"])
                prepared_item["_id"] = item["id"]

            if "_rev" in item:
                prepared_item["_rev"] = item.pop("_rev")

            if operation_type in (BaseOperationType.CREATE, BaseOperationType.INDEX):
                prepared_item["source"] = item

            elif operation_type == BaseOperationType.UPDATE:
                cls._check_item_for_update_or_delete_operation(prepared_item)
                prepared_item["source"] = item

            elif operation_type == BaseOperationType.DELETE:
                cls._check_item_for_update_or_delete_operation(prepared_item)
                prepared_item["_deleted"] = True

            prepared_data.append(prepared_item)

        return prepared_data

    def bulk_operation(
        self, target: str, data: Iterable[Dict], operation_type: BaseOperationType
    ) -> int:
        """Create, update, or delete multiple documents at the same time within a single request.

        Attributes:
            target (str): The target instance url with auth data.
            data (Iterable or IOBase): The data to write.
            operation_type (BaseOperationType): The mode of the write operation.

        Return:
            int: The number of written records.

        Raises:
            fastapi.HTTPException: When target is malformed.
            CozyStackError: see ralph.backends.cozystack.exceptions.
        """  # noqa: E501
        url = os.path.join("/", self.doctype, "_bulk_docs")
        prepared_data = self._prepare_data(data, operation_type)

        with CozyStackHttpClient(target=target) as client:
            response = client.post(url, json={"docs": prepared_data})
            check_cozystack_error(response)

        return len([item for item in response.json() if "error" not in item])

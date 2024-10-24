"""CozyStackDB data backend for Ralph."""

from __future__ import annotations

import logging
import os
from typing import Dict, Iterable, Iterator, List, Optional, TypeVar, Union

import httpx
from fastapi import HTTPException, status
from pydantic import StringConstraints, ValidationError
from pydantic_settings import SettingsConfigDict
from typing_extensions import Annotated

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    Listable,
    Writable,
)
from ralph.conf import BASE_SETTINGS_CONFIG, ClientOptions
from ralph.exceptions import BackendException
from ralph.models.cozy import CozyAuthData

logger = logging.getLogger(__name__)


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
            "Cookie": self.cozy_auth_data.cookie,
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

    def list_all_doctypes(self, target: str) -> List[str]:
        """List all doctypes available on targeted instance.

        Attributes:
            target (str): The target instance url with auth data.

        Return:
            List[str]: The doctypes available on targeted instance.

        Raises:
            fastapi.HTTPException: When target is malformed.
            httpx.HTTPError: When error during request
                or HTTP status of 4xx or 5xx.
        """
        with CozyStackHttpClient(target=target) as client:
            response = client.get("/_all_doctypes")
            response.raise_for_status()
            return response.json()

    def find(self, target: str, query: CozyStackQuery) -> Dict:
        """Find document using a mango selector.

        Attributes:
            target (str): The target instance url with auth data.
            query (CozyStackQuery): The query to select records to read.

        Return:
            Dict: Response containing records to read.

        Raises:
            fastapi.HTTPException: When target is malformed.
            httpx.HTTPError: When error during request
                or HTTP status of 4xx or 5xx.
        """
        url = os.path.join("/", self.doctype, "_find")

        with CozyStackHttpClient(target=target) as client:
            response = client.post(url, json=query.model_dump(exclude_none=True))
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _prepare_data(data: Iterable[dict], operation_type: BaseOperationType):
        """Enrich data based on operation type."""
        prepared_data = []

        for item in data:
            prepared_item = {"_id": item["id"]}

            if operation_type in (BaseOperationType.CREATE, BaseOperationType.INDEX):
                prepared_item["source"] = item

            elif operation_type == BaseOperationType.UPDATE:
                prepared_item["_rev"] = ""
                prepared_item["source"] = item

            elif operation_type == BaseOperationType.DELETE:
                prepared_item["_rev"] = ""
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
            httpx.HTTPError: When error during request
                or HTTP status of 4xx or 5xx.
        """  # noqa: E501
        url = os.path.join("/", self.doctype, "_bulk_docs")
        prepared_data = self._prepare_data(data, operation_type)

        with CozyStackHttpClient(target=target) as client:
            response = client.post(url, json={"docs": prepared_data})
            response.raise_for_status()

        return len(prepared_data)


class CozyStackClientOptions(ClientOptions):
    """CozyStack additional client options."""


class CozyStackDataBackendSettings(BaseDataBackendSettings):
    """CozyStack data backend default configuration.

    Attributes:
        DEFAULT_DOCTYPE (str): The default doctype to use for querying CozyStack.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(
            env_prefix="RALPH_BACKENDS__DATA__COZYSTACK__", regex_engine="python-re"
        ),
    }

    DEFAULT_DOCTYPE: Annotated[
        str, StringConstraints(pattern=r"(?:[a-z]+\.)+[a-z]+")
    ] = "com.inokufu.statements"

    CLIENT_OPTIONS: CozyStackClientOptions = CozyStackClientOptions()


class CozyStackQuery(BaseQuery):
    """CozyStack query model.

    Attributes:
        selector (dict): Filter query to select which documents to include.
        limit (int): Maximum number of results returned.
        skip (int): Skip the first ‘n’ results, where ‘n’ is the value specified.
        sort (list): List of (key, direction) pairs specifying the sort order.
        fields (dict): Dictionary specifying the fields to include or exclude.
        bookmark (str): Enable to specify which page of results you require.

    """

    selector: dict = {}

    limit: Optional[int] = None
    skip: Optional[int] = None

    sort: Optional[List[dict]] = None
    fields: Optional[List[str]] = None

    next: Optional[bool] = None
    bookmark: Optional[str] = None


Settings = TypeVar("Settings", bound=CozyStackDataBackendSettings)


class CozyStackDataBackend(
    BaseDataBackend[Settings, CozyStackQuery], Writable, Listable
):
    """CozyStack data backend."""

    name = "cozy-stack"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the CozyStack data backend.

        Args:
            settings (CozyStack DataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.client = CozyStackClient(self.settings.DEFAULT_DOCTYPE)

    def status(self) -> DataBackendStatus:
        """Check the CozyStack connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List doctypes in the `target` database.

        Args:
            target (str or None): The CozyStack instance to list doctypes from.
            details (bool): Get detailed collection information instead of just IDs.
            new (bool): Ignored.

        Yield:
            str: The next doctype name.

        Raise:
            BackendException: If a failure during the list operation occurs.
            BackendParameterException: If the `target` is not a valid database name.
        """
        if details:
            logger.warning("The `details` argument is ignored")

        if new:
            logger.warning("The `new` argument is ignored")

        try:
            yield from self.client.list_all_doctypes(target)
        except httpx.HTTPError as exc:
            msg = "Failed to list CozyStack doctypes: %s"
            logger.error(msg, exc)
            raise BackendException(msg % exc) from exc

    def _read_dicts(
        self,
        query: CozyStackQuery,
        target: Optional[str],
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        try:
            response = self.client.find(target, query)
            documents = response["docs"]

            # query object is used to pass next and bookmark
            query.next = response.get("next")
            query.bookmark = response.get("bookmark")

            yield from documents
        except httpx.HTTPError as exc:
            msg = "Failed to execute CozyStack query: %s"
            logger.error(msg, exc)
            logger.info(query)
            raise BackendException(msg % exc) from exc

    def _write_dicts(
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,  # noqa: ARG002
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        try:
            return self.client.bulk_operation(target, data, operation_type)
        except httpx.HTTPError as exc:
            msg = "Failed to insert data: %s"
            logger.error(msg, exc)
            raise BackendException(msg % exc) from exc

    def close(self) -> None:
        """CozyStack backend has no open connections to close. No action."""
        logger.info("No open connections to close; skipping")

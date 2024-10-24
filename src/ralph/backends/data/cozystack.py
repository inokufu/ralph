"""CozyStackDB data backend for Ralph."""

from __future__ import annotations

import logging
import os
from typing import Iterable, Iterator, List, Optional, TypeVar, Union

import httpx
from pydantic import StringConstraints
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


# TODO: CozyStack wrapper + dedicated exceptions


class CozyStackClient(object):
    """Wrapper of httpx.Client to request CozyStack."""
    def __init__(self, target: Optional[str]):
        """Instantiate the CozyStack client."""
        self.cozy_auth_data = CozyAuthData.model_validate_json(target)

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

    def status(self) -> DataBackendStatus:
        """Check the CozyStack connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        # TODO: GET /connection_check can't be done without target
        # DataBackendStatus.ERROR
        # DataBackendStatus.AWAY

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

        with CozyStackClient(target=target) as client:
            try:
                response = client.get("/_all_doctypes")
                response.raise_for_status()
                yield from response.json()
            except httpx.HTTPError as exc:
                msg = "Failed to list CozyStack doctypes: %s"
                logger.error(msg, exc)
                raise BackendException(msg % exc) from exc

    def _read_dicts(
        self,
        query: CozyStackQuery,
        target: Optional[str],
        chunk_size: int, # noqa: ARG002
        ignore_errors: bool, # noqa: ARG002
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        kwargs = query.model_dump(exclude_none=True)
        url = os.path.join("/", self.settings.DEFAULT_DOCTYPE, "_find")

        with CozyStackClient(target=target) as client:
            try:
                response = client.post(url, json=kwargs)
                response.raise_for_status()

                json_response = response.json()

                documents = json_response["docs"]

                # query object is used to pass next and bookmark
                query.next = json_response["next"]
                query.bookmark = json_response["bookmark"]

                yield from documents
            except httpx.HTTPError as exc:
                msg = "Failed to execute CozyStack query: %s"
                logger.error(msg, exc)
                raise BackendException(msg % exc) from exc


    def _write_dicts(
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int, # noqa: ARG002
        ignore_errors: bool, # noqa: ARG002
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        preparedData = []

        for item in data:
            preparedItem = {"_id": item["id"]}

            if operation_type in (BaseOperationType.CREATE, BaseOperationType.INDEX):
                preparedItem["source"] = item

            elif operation_type == BaseOperationType.UPDATE:
                preparedItem["_rev"] = ""
                preparedItem["source"] = item

            elif operation_type == BaseOperationType.DELETE:
                preparedItem["_rev"] = ""
                preparedItem["_deleted"] = True

            preparedData.append(preparedItem)

        url = os.path.join("/", self.settings.DEFAULT_DOCTYPE, "_bulk_docs")

        with CozyStackClient(target=target) as client:
            try:
                response = client.post(url, json={"docs": preparedData})
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = "Failed to insert data: %s"
                logger.error(msg, exc)
                raise BackendException(msg % exc) from exc

        return len(preparedData)

    def close(self) -> None:
        """CozyStack backend has no open connections to close. No action."""
        logger.info("No open connections to close; skipping")


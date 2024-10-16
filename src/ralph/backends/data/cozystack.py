"""CouchDB data backend for Ralph."""

from __future__ import annotations

import logging
import os
from typing import Generator, Iterable, Iterator, List, Optional, TypeVar, Union

import httpx
from pydantic_settings import SettingsConfigDict

from ralph.api.auth.cozy import CozyAuthData
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

logger = logging.getLogger(__name__)


# TODO: CozyStack wrapper + dedicated exceptions
# TODO: What happens if model validation error ?
class CozyStackClient(object):
    def __init__(self, target: Optional[str]):
        self.cozy_auth_data = CozyAuthData.model_validate_json(target)

    def __enter__(self) -> httpx.Client:
        base_url = os.path.join(self.cozy_auth_data["instance_url"], "data")

        headers = {
            "Accept": "application/json",
            "Authorization": self.cozy_auth_data["token"],
            "Cookie": self.cozy_auth_data["cookie"],
        }

        self.client = httpx.Client(base_url=base_url, headers=headers)

        return self.client

    def __exit__(self, *args):
        self.client.close()

class CozyStackClientOptions(ClientOptions):
    """CozyStack additional client options."""


class CozyStackDataBackendSettings(BaseDataBackendSettings):
    """CozyStack data backend default configuration.

    Attributes:
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(
            env_prefix="RALPH_BACKENDS__DATA__COZYSTACK__", regex_engine="python-re"
        ),
    }

    # TODO: add StringConstraints ?
    DEFAULT_DOCTYPE: str = "com.inokufu.statements"

    CLIENT_OPTIONS: CozyStackClientOptions = CozyStackClientOptions()


class CozyStackQuery(BaseQuery):
    """CozyStack query model.

    Attributes:
        selector (dict): Filter query to select which documents to include.
        limit (int): Maximum number of results returned.
        skip (int): Skip the first ‘n’ results, where ‘n’ is the value specified.
        sort (list): List of (key, direction) pairs specifying the sort order.
        fields (dict): Dictionary specifying the fields to include or exclude.
        bookmark (str): String that enables to specify which page of results you require.

    """

    selector: dict = {}
    limit: Optional[int] = None
    skip: Optional[int] = None
    sort: Optional[List[dict]] = None
    fields: Optional[List[str]] = None
    bookmark: Optional[str] = None


Settings = TypeVar("Settings", bound=CozyStackDataBackendSettings)


class CozyStackDataBackend(
    BaseDataBackend[Settings, CozyStackQuery], Writable, Listable
):
    """CozyStack data backend."""

    name = "cozy-stack"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the CozyStack client.

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
        # Check CozyStack server status.
        # TODO: GET /connection_check
        # TODO: can't be done without target
        # DataBackendStatus.ERROR
        # DataBackendStatus.AWAY

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List doctypes in the `target` database.

        Args:
            target (str or None): The CozyStack subdomain/instance to list doctypes from.
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

    # def read(
    #     self,
    #     query: Optional[CozyStackQuery] = None,
    #     target: Optional[str] = None,
    #     chunk_size: Optional[int] = None,
    #     raw_output: bool = False,
    #     ignore_errors: bool = False,
    #     max_statements: Optional[PositiveInt] = None,
    # ) -> Union[Iterator[bytes], Iterator[dict]]:
    #     """Read documents matching the `query` from `target` doctype and yield them.

    #     Args:
    #         query (CozyStackQuery): The CozyStack query to use when reading documents.
    #         target (str or None): The CozyStack doctype name to query.
    #             If target is `None`, the `DEFAULT_DOCTYPE` is used instead.
    #         chunk_size (int or None): The chunk size when reading archives by batch.
    #             If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
    #         raw_output (bool): Whether to yield dictionaries or bytes.
    #         ignore_errors (bool): If `True`, encoding errors during the read operation
    #             will be ignored and logged.
    #             If `False` (default), a `BackendException` is raised on any error.
    #         max_statements (int): The maximum number of statements to yield.
    #             If `None` (default) or `0`, there is no maximum.

    #     Yield:
    #         dict: If `raw_output` is False.
    #         bytes: If `raw_output` is True.
    #     Raise:
    #         BackendException: If a failure occurs during CouchDB connection or
    #             during encoding documents and `ignore_errors` is set to `False`.
    #         BackendParameterException: If the `target` is not a valid collection name.
    #     """
    #     yield from super().read(
    #         query, target, chunk_size, raw_output, ignore_errors, max_statements
    #     )


    # TODO: Manage limit & bookmark & next
    def _read_dicts(
        self,
        query: CozyStackQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        kwargs = query.model_dump(exclude_none=True)
        url = os.path.join("/", self.settings.DEFAULT_DOCTYPE, "_find")

        with CozyStackClient(target=target) as client:
            try:
                response = client.post(url, json=kwargs)
                response.raise_for_status()

                response = response.json()
                documents = response["docs"]

                yield from documents
            except httpx.HTTPError as exc:
                msg = "Failed to execute CozyStack query: %s"
                logger.error(msg, exc)
                raise BackendException(msg % exc) from exc

    # def write(
    #     self,
    #     data: Union[IOBase, Iterable[bytes], Iterable[dict]],
    #     target: Optional[str] = None,
    #     chunk_size: Optional[int] = None,
    #     ignore_errors: bool = False,
    #     operation_type: Optional[BaseOperationType] = None,
    # ) -> int:
    #     """Write `data` documents to the `target` collection and return their count.

    #     Args:
    #         data (Iterable or IOBase): The data containing documents to write.
    #         target (str or None): The target CouchDB collection name.
    #         chunk_size (int or None): The number of documents to write in one batch.
    #             If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
    #         ignore_errors (bool):  If `True`, errors during decoding, encoding and
    #             sending batches of documents are ignored and logged.
    #             If `False` (default), a `BackendException` is raised on any error.
    #         operation_type (BaseOperationType or None): The mode of the write operation.
    #             If `operation_type` is `None`, the `default_operation_type` is used
    #                 instead. See `BaseOperationType`.

    #     Return:
    #         int: The number of documents written.
    #     Raise:
    #         BackendException: If any failure occurs during the write operation or
    #             if an inescapable failure occurs and `ignore_errors` is set to `True`.
    #         BackendParameterException: If the `operation_type` is `APPEND` as it is not
    #             supported.
    #     """
    #     return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_dicts(
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        # NOTE: data already have an id cuz enrich in route

        # Create a document with a fixed id
        # PUT /data/:type/:id

        # Update a document
        # PUT /data/:type/:id

        # Delete a document
        # DELETE /data/:type/:id?rev=:rev

        # If create new => remove "id" from item
        # If update existing => add "_id", "_type", "_rev"

        # TODO: How to handle rev => check in statements route

        with CozyStackClient(target=target) as client:
            for item in data:
                url = os.path.join("/", self.settings.DEFAULT_DOCTYPE, item["id"])
                client.put(url, json=item)

    def close(self) -> None:
        """CozyStack backend has no open connections to close. No action."""
        logger.info("No open connections to close; skipping")

    @staticmethod
    def to_documents(
        data: Iterable[dict],
    ) -> Generator[dict, None, None]:
        """Convert `data` statements to CouchDB documents.
        We expect statements to have at least an `id` and a `timestamp` field that will
        be used to compute a unique CouchDB Object ID. This ensures that we will not
        duplicate statements in our database and allows us to support pagination.
        """
        for statement in data:
            yield {
                "_id": statement.get("id", None),
                "source": statement,
            }

    @staticmethod
    def _count(statements: Iterable, counter: dict) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            yield statement
            counter["count"] += 1

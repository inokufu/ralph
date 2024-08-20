"""CouchDB data backend for Ralph."""

from __future__ import annotations

import logging
from io import IOBase
from typing import Generator, Iterable, Iterator, List, Optional, TypeVar, Union

from couchdb import Database, Server, ServerError
from pydantic import HttpUrl, PositiveInt, StringConstraints
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
from ralph.exceptions import BackendException, BackendParameterException

logger = logging.getLogger(__name__)


class CouchClientOptions(ClientOptions):
    """CouchDB additional client options."""


class CouchDataBackendSettings(BaseDataBackendSettings):
    """CouchDB data backend default configuration.

    Attributes:
        CONNECTION_URI (str): The CouchDB connection URI.
        DEFAULT_DATABASE (str): The CouchDB database to connect to.
        CLIENT_OPTIONS (CouchClientOptions): A dictionary of CouchDB client options.
        LOCALE_ENCODING (str): The locale encoding to use when none is provided.
        READ_CHUNK_SIZE (int): The default chunk size for reading batches of documents.
        WRITE_CHUNK_SIZE (int): The default chunk size for writing batches of documents.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(
            env_prefix="RALPH_BACKENDS__DATA__COUCH__", regex_engine="python-re"
        ),
    }  # We specify regex_engine as some regex are no longer supported in Pydantic V2

    # TODO: These env variables are not taken into account in the code
    CONNECTION_URI: HttpUrl = HttpUrl("http://admin:password@couch:5984/")
    DEFAULT_DATABASE: Annotated[
        str, StringConstraints(pattern=r"^[^\s.$/\\\"\x00]+$")
    ] = "statements"
    CLIENT_OPTIONS: CouchClientOptions = CouchClientOptions()


class CouchQuery(BaseQuery):
    """CouchDB query model.

    Attributes:
        selector (dict): A filter query to select which documents to include.
        limit (int): The maximum number of results to return.
        fields (dict): Dictionary specifying the fields to include or exclude.
        sort (list): A list of (key, direction) pairs specifying the sort order.
    """

    selector: dict = {}
    limit: Optional[int] = None
    fields: Optional[dict] = None
    sort: Optional[List[dict]] = None
    bookmark: Optional[str] = None


Settings = TypeVar("Settings", bound=CouchDataBackendSettings)


class CouchDataBackend(BaseDataBackend[Settings, CouchQuery], Writable, Listable):
    """CouchDB data backend."""

    name = "couch"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Optional[Settings] = None):
        """Instantiate the CouchDB client.

        Args:
            settings (CouchDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        host = str(self.settings.CONNECTION_URI)
        self.client = Server(host, **self.settings.CLIENT_OPTIONS.model_dump())
        self.database = self.client[self.settings.DEFAULT_DATABASE]

    def status(self) -> DataBackendStatus:
        """Check the CouchDB connection status.

        Return:
            DataBackendStatus: The status of the data backend.
        """
        # Check CouchDB server status.
        try:
            if self.client.resource.get_json('/_up').get("status") != 'ok':
                logger.error("CouchDB `_up` endpoint did not return 'ok'")
                return DataBackendStatus.ERROR
        except Exception as error:
            logger.error("Failed to connect to CouchDB: %s", error)
            return DataBackendStatus.AWAY

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List collections in the `target` database.

        Args:
            target (str or None): The MongoDB database name to list collections from.
                If target is `None`, the `DEFAULT_DATABASE` is used instead.
            details (bool): Get detailed collection information instead of just IDs.
            new (bool): Ignored.

        Raise:
            BackendException: If a failure during the list operation occurs.
            BackendParameterException: If the `target` is not a valid database name.
        """
        if new:
            logger.warning("The `new` argument is ignored")

        if target:
            logger.warning("The `target` argument is ignored")

        try:
            yield from self.client.resource.get_json('/_all_dbs')
        except ServerError as error:
            msg = "Failed to list CouchDB collections: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    def read(  # noqa: PLR0913
        self,
        query: Optional[CouchQuery] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read documents matching the `query` from `target` collection and yield them.

        Args:
            query (CouchQuery): The CouchDB query to use when reading documents.
            target (str or None): The CouchDB collection name to query.
                If target is `None`, the `DEFAULT_COLLECTION` is used instead.
            chunk_size (int or None): The chunk size when reading archives by batch.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
            raw_output (bool): Whether to yield dictionaries or bytes.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default) or `0`, there is no maximum.

        Yield:
            dict: If `raw_output` is False.
            bytes: If `raw_output` is True.

        Raise:
            BackendException: If a failure occurs during CouchDB connection or
                during encoding documents and `ignore_errors` is set to `False`.
            BackendParameterException: If the `target` is not a valid collection name.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_dicts(
        self,
        query: CouchQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        kwargs = query.model_dump(exclude_none=True)
        database = self._get_target_database(target)
        try:
            _, _, response = database.resource.post_json(path='_find', body=kwargs)
            documents = response['docs']
            bookmark = response.get('bookmark', None)
            yield from (d.update({"bookmark": bookmark}) or d for d in documents)
        except (ServerError, IndexError, TypeError, ValueError) as error:
            msg = "Failed to execute CouchDB query: %s"
            logger.error(msg, error)
            raise BackendException(msg % error) from error

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write `data` documents to the `target` collection and return their count.

        Args:
            data (Iterable or IOBase): The data containing documents to write.
            target (str or None): The target CouchDB collection name.
            chunk_size (int or None): The number of documents to write in one batch.
                If `chunk_size` is `None` it defaults to `WRITE_CHUNK_SIZE`.
            ignore_errors (bool):  If `True`, errors during decoding, encoding and
                sending batches of documents are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If `operation_type` is `None`, the `default_operation_type` is used
                    instead. See `BaseOperationType`.

        Return:
            int: The number of documents written.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If the `operation_type` is `APPEND` as it is not
                supported.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        database = self._get_target_database(target)
        counter = {"count": 0}
        data = self._count(data, counter)
        
        if operation_type == BaseOperationType.UPDATE:
            database.update(list(self.to_documents(data)))
            logger.info("Updated the document with success")
        elif operation_type == BaseOperationType.DELETE:
            # TODO: Ne fonctionne pas pour une liste
            database.delete(list(self.to_documents(data)))
            logger.info("Deleted the document with success")
        else:
            database.update(list(self.to_documents(data)))
            logger.info("Inserted the document with success")

        return counter["count"]

    def close(self) -> None:
        """CouchDB backend has no open connections to close. No action."""
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

    def _get_target_database(self, target: Union[str, None]) -> Database:
        """Return the validated target database."""
        try:
            return self.client[target] if target else self.database
        # except InvalidName as error:
        # TODO: Check if the error is well caught
        except Exception as error:
            msg = "The target=`%s` is not a valid database name: %s"
            logger.error(msg, target, error)
            raise BackendParameterException(msg % (target, error)) from error

    @staticmethod
    def _count(statements: Iterable, counter: dict) -> Iterator:
        """Count the elements in the `statements` Iterable and yield element."""
        for statement in statements:
            yield statement
            counter["count"] += 1

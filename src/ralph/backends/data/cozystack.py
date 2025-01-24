"""CozyStackDB data backend for Ralph."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Annotated, TypeVar

from fastapi import HTTPException, status
from pydantic import NonNegativeInt, StringConstraints
from pydantic_settings import SettingsConfigDict

from ralph.backends.cozystack import CozyStackClient, CozyStackError
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
from ralph.utils import check_dict_keys

logger = logging.getLogger(__name__)


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
    ] = "io.cozy.learningrecords"

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

    selector: Mapping = {}

    limit: NonNegativeInt | None = None
    skip: NonNegativeInt | None = None

    sort: Sequence[Mapping] | None = None
    fields: Sequence[str] | None = None

    next: bool | None = None
    bookmark: str | None = None


Settings = TypeVar("Settings", bound=CozyStackDataBackendSettings)


class CozyStackDataBackend(
    BaseDataBackend[Settings, CozyStackQuery], Writable, Listable
):
    """CozyStack data backend."""

    name = "cozy-stack"
    unsupported_operation_types = {BaseOperationType.APPEND}

    def __init__(self, settings: Settings | None = None):
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
        self, target: str | None = None, details: bool = False, new: bool = False
    ) -> Iterator[str] | Iterator[dict]:
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
        except CozyStackError as exc:
            msg = "Failed to list CozyStack doctypes: %s"
            logger.error(msg, exc)
            raise BackendException(msg % exc) from exc

    def _read_dicts(
        self,
        query: CozyStackQuery,
        target: str | None,
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        if ignore_errors:
            logger.warning("The `ignore_errors` argument is ignored")

        if target is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CozyStack backend must be used with Cozy authentication system",
            )

        try:
            response = self.client.find(target, query.model_dump(exclude_none=True))
            documents = response["docs"]

            # query object is used to pass next and bookmark
            query.next = response.get("next")
            query.bookmark = response.get("bookmark")

            yield from documents
        except CozyStackError as exc:
            msg = "Failed to execute CozyStack query: %s"
            logger.error(msg, exc)
            raise BackendException(msg % exc) from exc

    @staticmethod
    def to_documents(
        data: Iterable[Mapping],
        operation_type: BaseOperationType,
    ) -> Iterator[dict]:
        """Convert dictionaries from to documents ready to insert and yield them."""
        if operation_type in (BaseOperationType.CREATE, BaseOperationType.INDEX):
            for item in data:
                document = {"source": item}

                if "id" in item:
                    document["_id"] = item["id"]

                yield document

        elif operation_type == BaseOperationType.UPDATE:
            for item in data:
                check_dict_keys(item, ["id", "_rev"])

                yield {
                    "_id": item.get("id"),
                    "_rev": item.pop("_rev"),
                    "source": item,
                }

        elif operation_type == BaseOperationType.DELETE:
            for item in data:
                check_dict_keys(item, ["id", "_rev"])

                yield {
                    "_id": item.get("id"),
                    "_rev": item.pop("_rev"),
                    "_deleted": True,
                }

    def _write_dicts(
        self,
        data: Iterable[Mapping],
        target: str | None,
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,  # noqa: ARG002
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        try:
            documents = self.to_documents(data, operation_type)
            count = self.client.bulk_operation(target, documents, operation_type)
            logger.info("Finished writing %d documents with success", count)
            return count
        except (CozyStackError, ValueError) as exc:
            msg = "Failed to insert data: %s"
            logger.error(msg, exc)
            raise BackendException(msg % exc) from exc

    def close(self) -> None:
        """CozyStack backend has no open connections to close. No action."""
        logger.info("No open connections to close; skipping")

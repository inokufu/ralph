"""Base LRS backend for Ralph."""

import logging
from abc import abstractmethod
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Annotated,
    Any,
    Literal,
    TypeVar,
)
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    NonNegativeInt,
    StrictBool,
    TypeAdapter,
    conlist,
    constr,
)
from pydantic_settings import SettingsConfigDict

from ralph.backends.data.base import (
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    Writable,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.exceptions import BackendException
from ralph.models.xapi.base.agents import BaseXapiAgent
from ralph.models.xapi.base.common import IRI
from ralph.models.xapi.base.groups import BaseXapiGroup
from ralph.models.xapi.base.statements import check_statement_is_voiding

logger = logging.getLogger(__name__)


class BaseLRSBackendSettings(BaseDataBackendSettings):
    """LRS backend default configuration."""

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__"),
    }


@dataclass
class StatementQueryResult:
    """Result of an LRS statements query."""

    statements: Sequence[Mapping]
    pit_id: str | None = None
    search_after: str | None = None


def validate_iso_datetime_str(value: str | datetime) -> datetime:
    """Value is expected to be an ISO 8601 date time string.

    Note that we also accept datetime python instance that will be converted
    to an ISO 8601 date time string.
    """
    if not isinstance(value, (str, datetime)):
        raise ValueError("a string or datetime is required")

    if isinstance(value, datetime):
        return value.isoformat()

    # Validate iso-string
    try:
        datetime.fromisoformat(value)
    except ValueError as err:
        raise ValueError("invalid ISO 8601 date time string") from err


IsoDatetimeStr = Annotated[str | datetime, AfterValidator(validate_iso_datetime_str)]


class LRSStatementsQuery(BaseQuery):
    """Pydantic model for LRS query on Statements resource query parameters.

    LRS Specification:
    https://github.com/adlnet/xAPI-Spec/blob/1.0.3/xAPI-Communication.md#213-get-statements
    """

    statement_id: Annotated[str | None, Field(alias="statementId")] = None
    voided_statement_id: Annotated[str | None, Field(alias="voidedStatementId")] = None
    agent: BaseXapiAgent | BaseXapiGroup | None = None
    verb: IRI | None = None
    activity: IRI | None = None
    registration: UUID | None = None
    related_activities: bool | None = False
    related_agents: bool | None = False
    since: IsoDatetimeStr | None = None
    until: IsoDatetimeStr | None = None
    limit: NonNegativeInt | None = 0
    format: Literal["ids", "exact", "canonical"] | None = "exact"
    attachments: bool | None = False
    ascending: bool | None = False


class AgentParameters(BaseModel):
    """LRS query parameters for query on type Agent.

    NB: Agent refers to the data structure, NOT to the LRS query parameter.
    """

    mbox: str | None = None
    mbox_sha1sum: str | None = None
    openid: str | None = None
    account__name: str | None = None
    account__home_page: str | None = None


class RalphStatementsQuery(LRSStatementsQuery):
    """Represents a dictionary of possible LRS query parameters."""

    agent: AgentParameters | None = None
    search_after: str | None = None
    pit_id: str | None = None
    authority: AgentParameters | None = None
    ignore_order: bool | None = None


Settings = TypeVar("Settings", bound=BaseLRSBackendSettings)

NonEmptyStr = constr(strict=True, min_length=1)

params_adapter = TypeAdapter(RalphStatementsQuery)
ids_adapter = TypeAdapter(Sequence[NonEmptyStr])
target_adapter = TypeAdapter(NonEmptyStr | None)
include_extra_adapter = TypeAdapter(StrictBool)
statements_adapter = TypeAdapter(conlist(dict, min_length=1))
statements_ids_adapter = TypeAdapter(conlist(NonEmptyStr, min_length=1))


def _check_voided_statements(
    voided_statements_with_extra: Sequence[Mapping],
    voided_statements_ids: Sequence[str],
) -> list[dict]:
    """Check if statements can be voided.

    Args:
        voided_statements_with_extra: List of statements fetched
            from the database (with extra data).
        voided_statements_ids: List of statements ids that are
            supposed to be voided.

    Returns:
        List of statements safe to void.

    Raises:
        BackendException: When some voided statements are not valid:
            - a voiding Statement references a Statement that does not exist,
            - a voiding Statement references another voiding Statement,
            - a voiding Statement references a Statement that has already been voided.
    """
    voided_statements_with_extra_as_dict = {
        extra_statement["statement"]["id"]: extra_statement
        for extra_statement in voided_statements_with_extra
    }

    statements = []

    for statement_id in voided_statements_ids:
        if statement_id not in voided_statements_with_extra_as_dict:
            msg = (
                f"StatementRef '{statement_id}' of voiding Statement "
                "references a Statement that does not exist"
            )

            logger.error(msg)
            raise BackendException(msg)

        extra_statement = voided_statements_with_extra_as_dict[statement_id]
        statement = extra_statement["statement"]
        metadata = extra_statement["metadata"]

        if check_statement_is_voiding(statement):
            msg = (
                f"StatementRef '{statement_id}' of voiding Statement "
                "references another voiding Statement"
            )

            logger.error(msg)
            raise BackendException(msg)

        if metadata["voided"]:
            msg = (
                f"StatementRef '{statement['id']}' of voiding Statement "
                "references a Statement that has already been voided"
            )

            logger.error(msg)
            raise BackendException(msg)

        statements.append(statement)

    return statements


class BaseLRSBackend(BaseDataBackend[Settings, Any], Writable):
    """Base LRS backend interface."""

    @abstractmethod
    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""

    def index_statements(
        self, statements: Sequence[Mapping], target: str | None = None
    ) -> int:
        """Index statements as not voided on given target.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        statements = statements_adapter.validate_python(statements)
        target_adapter.validate_python(target)

        return self.write(
            data=statements,
            metadata={"voided": False},
            target=target,
            ignore_errors=False,
            operation_type=BaseOperationType.INDEX,
        )

    def void_statements(
        self, voided_statements_ids: Sequence[str], target: str | None = None
    ) -> int:
        """Void statements corresponding to voided_statements_ids on given target.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        voided_statements_ids = statements_ids_adapter.validate_python(
            voided_statements_ids
        )
        target_adapter.validate_python(target)

        voided_statements_with_extra = self.query_statements_by_ids(
            ids=voided_statements_ids,
            target=target,
            include_extra=True,
        )

        statements = _check_voided_statements(
            voided_statements_with_extra, voided_statements_ids
        )

        return self.write(
            data=statements,
            metadata={"voided": True},
            target=target,
            ignore_errors=False,
            operation_type=BaseOperationType.UPDATE,
        )


class BaseAsyncLRSBackend(BaseAsyncDataBackend[Settings, Any], AsyncWritable):
    """Base async LRS backend interface."""

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> AsyncIterator[dict]:
        """Return the list of matching statement IDs from the database."""

    async def index_statements(
        self, statements: Sequence[Mapping], target: str | None = None
    ) -> int:
        """Index statements as not voided on given target.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        statements = statements_adapter.validate_python(statements)
        target_adapter.validate_python(target)

        return await self.write(
            data=statements,
            metadata={"voided": False},
            target=target,
            ignore_errors=False,
            operation_type=BaseOperationType.INDEX,
        )

    async def void_statements(
        self, voided_statements_ids: Sequence[str], target: str | None = None
    ) -> int:
        """Void statements corresponding to voided_statements_ids on given target.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
            BackendParameterException: If a backend argument value is not valid.
        """
        voided_statements_ids = statements_ids_adapter.validate_python(
            voided_statements_ids
        )
        target_adapter.validate_python(target)

        voided_statements_with_extra = [
            statement
            async for statement in self.query_statements_by_ids(
                ids=voided_statements_ids,
                target=target,
                include_extra=True,
            )
        ]

        statements = _check_voided_statements(
            voided_statements_with_extra, voided_statements_ids
        )

        return await self.write(
            data=statements,
            metadata={"voided": True},
            target=target,
            ignore_errors=False,
            operation_type=BaseOperationType.UPDATE,
        )

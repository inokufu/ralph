"""Base LRS backend for Ralph."""

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

from pydantic import AfterValidator, BaseModel, Field, NonNegativeInt
from pydantic_settings import SettingsConfigDict

from ralph.backends.data.base import (
    BaseAsyncDataBackend,
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseQuery,
)
from ralph.conf import BASE_SETTINGS_CONFIG
from ralph.models.xapi.base.agents import BaseXapiAgent
from ralph.models.xapi.base.common import IRI
from ralph.models.xapi.base.groups import BaseXapiGroup


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


class BaseLRSBackend(BaseDataBackend[Settings, Any]):
    """Base LRS backend interface."""

    @abstractmethod
    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None
    ) -> Iterator[dict]:
        """Yield statements with matching ids from the backend."""


class BaseAsyncLRSBackend(BaseAsyncDataBackend[Settings, Any]):
    """Base async LRS backend interface."""

    @abstractmethod
    async def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""

    @abstractmethod
    async def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None
    ) -> AsyncIterator[dict]:
        """Return the list of matching statement IDs from the database."""

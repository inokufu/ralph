"""FileSystem LRS backend for Ralph."""

import logging
from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import datetime
from io import IOBase
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic_settings import SettingsConfigDict

from ralph.backends.data.base import BaseOperationType
from ralph.backends.data.fs import FSDataBackend, FSDataBackendSettings
from ralph.backends.lrs.base import (
    AgentParameters,
    BaseLRSBackend,
    BaseLRSBackendSettings,
    RalphStatementsQuery,
    StatementQueryResult,
    ids_adapter,
    include_extra_adapter,
    params_adapter,
    target_adapter,
)
from ralph.conf import BASE_SETTINGS_CONFIG

logger = logging.getLogger(__name__)


class FSLRSBackendSettings(BaseLRSBackendSettings, FSDataBackendSettings):
    """FileSystem LRS backend default configuration.

    Attributes:
        DEFAULT_LRS_FILE (str): The default LRS filename to store statements.
    """

    model_config = {
        **BASE_SETTINGS_CONFIG,
        **SettingsConfigDict(env_prefix="RALPH_BACKENDS__LRS__FS__"),
    }

    DEFAULT_LRS_FILE: str = "fs_lrs.jsonl"


class FSLRSBackend(BaseLRSBackend[FSLRSBackendSettings], FSDataBackend):
    """FileSystem LRS Backend."""

    def write(  # noqa: PLR0913
        self,
        data: IOBase | Iterable[bytes] | Iterable[Mapping],
        metadata: Mapping | None = None,
        target: str | None = None,
        chunk_size: int | None = None,
        ignore_errors: bool = False,
        operation_type: BaseOperationType | None = None,
    ) -> int:
        """Write data records to the target file and return their count.

        See `FSDataBackend.write`.
        """
        if target:
            target = str(Path(target) / Path(self.settings.DEFAULT_LRS_FILE))
        else:
            target = self.settings.DEFAULT_LRS_FILE

        return super().write(
            data, metadata, target, chunk_size, ignore_errors, operation_type
        )

    def query_statements(
        self, params: RalphStatementsQuery, target: str | None = None
    ) -> StatementQueryResult:
        """Return the statements query payload using xAPI parameters."""
        params_adapter.validate_python(params)
        target_adapter.validate_python(target)

        filters = []

        if params.statement_id:
            self._add_filter_by_id(filters, params.statement_id)
        elif params.voided_statement_id:
            self._add_filter_by_voided_id(filters, params.voided_statement_id)

        self._add_filter_by_agent(filters, params.agent, params.related_agents)
        self._add_filter_by_authority(filters, params.authority)
        self._add_filter_by_verb(filters, params.verb)
        self._add_filter_by_activity(
            filters, params.activity, params.related_activities
        )
        self._add_filter_by_registration(filters, params.registration)
        self._add_filter_by_timestamp_since(filters, params.since)
        self._add_filter_by_timestamp_until(filters, params.until)
        self._add_filter_by_search_after(filters, params.search_after)

        limit = params.limit
        statements_count = 0
        search_after = None
        statements = []
        for item in self.read(query=self.settings.DEFAULT_LRS_FILE, target=target):
            for query_filter in filters:
                if not query_filter(item):
                    break
            else:
                statements.append(item.get("statement"))
                statements_count += 1
                if limit and statements_count == limit:
                    search_after = statements[-1].get("id")
                    break

        if params.ascending:
            statements.reverse()
        return StatementQueryResult(
            statements=statements,
            pit_id=None,
            search_after=search_after,
        )

    def query_statements_by_ids(
        self, ids: Sequence[str], target: str | None = None, include_extra: bool = False
    ) -> Iterator[dict]:
        """Return the list of matching statement IDs from the database."""
        ids_adapter.validate_python(ids)
        target_adapter.validate_python(target)
        include_extra_adapter.validate_python(include_extra)

        statement_ids = set(ids)

        for item in self.read(query=self.settings.DEFAULT_LRS_FILE, target=target):
            statement = item.get("statement")

            if statement.get("id") in statement_ids:
                if include_extra:
                    yield item
                else:
                    yield statement

    @staticmethod
    def _add_filter_by_agent(
        filters: Sequence, agent: AgentParameters | Mapping | None, related: bool | None
    ) -> None:
        """Add agent filters to `filters` if `agent` is set."""
        if not agent:
            return

        if not isinstance(agent, Mapping):
            agent = agent.model_dump()

        FSLRSBackend._add_filter_by_mbox(filters, agent.get("mbox", None), related)
        FSLRSBackend._add_filter_by_sha1sum(
            filters, agent.get("mbox_sha1sum", None), related
        )
        FSLRSBackend._add_filter_by_openid(filters, agent.get("openid", None), related)
        FSLRSBackend._add_filter_by_account(
            filters,
            agent.get("account__name", None),
            agent.get("account__home_page", None),
            related,
        )

    @staticmethod
    def _add_filter_by_authority(
        filters: Sequence,
        authority: AgentParameters | Mapping | None,
    ) -> None:
        """Add authority filters to `filters` if `authority` is set."""
        if not authority:
            return

        if not isinstance(authority, Mapping):
            authority = authority.model_dump()

        FSLRSBackend._add_filter_by_mbox(
            filters, authority.get("mbox", None), field="authority"
        )
        FSLRSBackend._add_filter_by_sha1sum(
            filters, authority.get("mbox_sha1sum", None), field="authority"
        )
        FSLRSBackend._add_filter_by_openid(
            filters, authority.get("openid", None), field="authority"
        )
        FSLRSBackend._add_filter_by_account(
            filters,
            authority.get("account__name", None),
            authority.get("account__home_page", None),
            field="authority",
        )

    @staticmethod
    def _add_filter_by_id(filters: Sequence, statement_id: str | None) -> None:
        """Add the `match_statement_id` filter if `statement_id` is set."""

        def match_statement_id(item: Mapping) -> bool:
            """Return `True` if the statement has the given `statement_id`."""
            return (
                item.get("statement")["id"] == statement_id
                and not item.get("metadata")["voided"]
            )

        if statement_id:
            filters.append(match_statement_id)

    @staticmethod
    def _add_filter_by_voided_id(filters: Sequence, statement_id: str | None) -> None:
        """Add the `match_statement_id` filter if `voided_statement_id` is set."""

        def match_voided_statement_id(item: Mapping) -> bool:
            """Return `True` if the statement has the given `statement_id`."""
            return (
                item.get("statement")["id"] == statement_id
                and item.get("metadata")["voided"]
            )

        if statement_id:
            filters.append(match_voided_statement_id)

    @staticmethod
    def _get_related_agents(statement: Mapping) -> Iterable[Mapping]:
        yield statement.get("actor", {})
        yield statement.get("object", {})
        yield statement.get("authority", {})
        context = statement.get("context", {})
        yield context.get("instructor", {})
        yield context.get("team", {})

    @staticmethod
    def _add_filter_by_mbox(
        filters: Sequence,
        mbox: str | None,
        related: bool | None = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_mbox` filter if `mbox` is set."""

        def match_mbox(item: Mapping) -> bool:
            """Return `True` if the statement has the given `actor.mbox`."""
            return item.get("statement").get(field, {}).get("mbox") == mbox

        def match_related_mbox(item: Mapping) -> bool:
            """Return `True` if the statement has any agent matching `mbox`."""
            if "statement" in item:
                statement = item.get("statement")

            elif item.get("objectType") == "SubStatement":
                statement = item

            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("mbox") == mbox:
                    return True

            statement_object = statement.get("object", {})

            if statement_object.get("objectType") == "SubStatement":
                return match_related_mbox(statement_object)

            return False

        if mbox:
            filters.append(match_related_mbox if related else match_mbox)

    @staticmethod
    def _add_filter_by_sha1sum(
        filters: Sequence,
        sha1sum: str | None,
        related: bool | None = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_sha1sum` filter if `sha1sum` is set."""

        def match_sha1sum(item: Mapping) -> bool:
            """Return `True` if the statement has the given `actor.sha1sum`."""
            return item.get("statement").get(field, {}).get("mbox_sha1sum") == sha1sum

        def match_related_sha1sum(item: Mapping) -> bool:
            """Return `True` if the statement has any agent matching `sha1sum`."""
            if "statement" in item:
                statement = item.get("statement")

            elif item.get("objectType") == "SubStatement":
                statement = item

            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("mbox_sha1sum") == sha1sum:
                    return True

            statement_object = statement.get("object", {})

            if statement_object.get("objectType") == "SubStatement":
                return match_related_sha1sum(statement_object)

            return False

        if sha1sum:
            filters.append(match_related_sha1sum if related else match_sha1sum)

    @staticmethod
    def _add_filter_by_openid(
        filters: Sequence,
        openid: str | None,
        related: bool | None = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_openid` filter if `openid` is set."""

        def match_openid(item: Mapping) -> bool:
            """Return `True` if the statement has the given `actor.openid`."""
            return item.get("statement").get(field, {}).get("openid") == openid

        def match_related_openid(item: Mapping) -> bool:
            """Return `True` if the statement has any agent matching `openid`."""
            if "statement" in item:
                statement = item.get("statement")

            elif item.get("objectType") == "SubStatement":
                statement = item

            for agent in FSLRSBackend._get_related_agents(statement):
                if agent.get("openid") == openid:
                    return True

            statement_object = statement.get("object", {})

            if statement_object.get("objectType") == "SubStatement":
                return match_related_openid(statement_object)

            return False

        if openid:
            filters.append(match_related_openid if related else match_openid)

    @staticmethod
    def _add_filter_by_account(
        filters: Sequence,
        name: str | None,
        home_page: str | None,
        related: bool | None = False,
        field: Literal["actor", "authority"] = "actor",
    ) -> None:
        """Add the `match_account` filter if `name` or `home_page` is set."""

        def match_account(item: Mapping) -> bool:
            """Return `True` if the statement has the given `actor.account`."""
            account = item.get("statement").get(field, {}).get("account", {})
            return account.get("name") == name and account.get("homePage") == home_page

        def match_related_account(item: Mapping) -> bool:
            """Return `True` if the statement has any agent matching the account."""
            if "statement" in item:
                statement = item.get("statement")

            elif item.get("objectType") == "SubStatement":
                statement = item

            for agent in FSLRSBackend._get_related_agents(statement):
                account = agent.get("account", {})
                if account.get("name") == name and account.get("homePage") == home_page:
                    return True

            statement_object = statement.get("object", {})

            if statement_object.get("objectType") == "SubStatement":
                return match_related_account(statement_object)

            return False

        if name and home_page:
            filters.append(match_related_account if related else match_account)

    @staticmethod
    def _add_filter_by_verb(filters: Sequence, verb_id: str | None) -> None:
        """Add the `match_verb_id` filter if `verb_id` is set."""

        def match_verb_id(item: Mapping) -> bool:
            """Return `True` if the statement has the given `verb.id`."""
            return item.get("statement").get("verb", {}).get("id") == verb_id

        if verb_id:
            filters.append(match_verb_id)

    @staticmethod
    def _add_filter_by_activity(
        filters: Sequence, object_id: str | None, related: bool | None
    ) -> None:
        """Add the `match_object_id` filter if `object_id` is set."""

        def match_object_id(item: Mapping) -> bool:
            """Return `True` if the statement has the given `object.id`."""
            return item.get("statement").get("object", {}).get("id") == object_id

        def match_related_object_id(item: Mapping) -> bool:
            """Return `True` if the statement has any object.id matching `object_id`."""
            if "statement" in item:
                statement = item.get("statement")

            elif item.get("objectType") == "SubStatement":
                statement = item

            statement_object = statement.get("object", {})

            if statement_object.get("id") == object_id:
                return True

            activities = statement.get("context", {}).get("contextActivities", {})

            for activity in activities.values():
                if isinstance(activity, Mapping):
                    if activity.get("id") == object_id:
                        return True
                else:
                    for sub_activity in activity:
                        if sub_activity.get("id") == object_id:
                            return True

            if statement_object.get("objectType") == "SubStatement":
                return match_related_object_id(statement_object)

            return False

        if object_id:
            filters.append(match_related_object_id if related else match_object_id)

    def _add_filter_by_timestamp_since(
        self, filters: Sequence, timestamp: datetime | None
    ) -> None:
        """Add the `match_since` filter if `timestamp` is set."""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        def match_since(item: Mapping) -> bool:
            """Return `True` if the statement was created after `timestamp`."""
            statement = item.get("statement")

            try:
                statement_timestamp = datetime.fromisoformat(statement.get("timestamp"))
            except (TypeError, ValueError) as error:
                msg = "Statement with id=%s contains unparsable timestamp=%s"
                logger.debug(msg, statement.get("id"), error)
                return False
            return statement_timestamp > timestamp

        if timestamp:
            filters.append(match_since)

    def _add_filter_by_timestamp_until(
        self, filters: Sequence, timestamp: datetime | None
    ) -> None:
        """Add the `match_until` function if `timestamp` is set."""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        def match_until(item: Mapping) -> bool:
            """Return `True` if the statement was created before `timestamp`."""
            statement = item.get("statement")

            try:
                statement_timestamp = datetime.fromisoformat(statement.get("timestamp"))
            except (TypeError, ValueError) as error:
                msg = "Statement with id=%s contains unparsable timestamp=%s"
                logger.debug(msg, statement.get("id"), error)
                return False

            return statement_timestamp <= timestamp

        if timestamp:
            filters.append(match_until)

    @staticmethod
    def _add_filter_by_search_after(
        filters: Sequence, search_after: str | None
    ) -> None:
        """Add the `match_search_after` filter if `search_after` is set."""
        search_after_state = {"state": False}

        def match_search_after(item: Mapping) -> bool:
            """Return `True` if the statement was created after `search_after`."""
            if search_after_state["state"]:
                return True
            if item.get("statement").get("id") == search_after:
                search_after_state["state"] = True
            return False

        if search_after:
            filters.append(match_search_after)

    @staticmethod
    def _add_filter_by_registration(
        filters: Sequence, registration: UUID | None
    ) -> None:
        """Add the `match_registration` filter if `registration` is set."""
        registration_str = str(registration)

        def match_registration(item: Mapping) -> bool:
            """Return `True` if the statement has the given `context.registration`."""
            return (
                item.get("statement").get("context", {}).get("registration")
                == registration_str
            )

        if registration:
            filters.append(match_registration)

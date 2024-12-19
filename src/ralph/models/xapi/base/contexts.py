"""Base xAPI `Context` definitions."""

from uuid import UUID

from pydantic import Field

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .common import IRI, LanguageTag
from .groups import BaseXapiGroup
from .unnested_objects import BaseXapiActivity, BaseXapiStatementRef


class BaseXapiContextContextActivities(BaseModelWithConfig):
    """Pydantic model for context `contextActivities` property.

    Attributes:
        parent (dict or list): An Activity with a direct relation to the statement's
            Activity.
        grouping (dict or list): An Activity with an indirect relation to the
            statement's Activity.
        category (dict or list): An Activity used to categorize the Statement.
        other (dict or list): A contextActivity that doesn't fit one of the other
            properties.
    """

    parent: BaseXapiActivity | list[BaseXapiActivity] | None = None
    grouping: BaseXapiActivity | list[BaseXapiActivity] | None = None
    category: BaseXapiActivity | list[BaseXapiActivity] | None = None
    other: BaseXapiActivity | list[BaseXapiActivity] | None = None


class BaseXapiContext(BaseModelWithConfig):
    """Pydantic model for `context` property.

    Attributes:
        registration (UUID): The registration that the Statement is associated with.
        instructor (dict): The instructor that the Statement relates to.
        team (dict): The team that this Statement relates to.
        contextActivities (dict): See BaseXapiContextContextActivities.
        revision (str): The revision of the activity associated with this Statement.
        platform (str): The platform where the learning activity took place.
        language (dict): The language in which the experience occurred.
        statement (dict): Another Statement giving context for this Statement.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    registration: UUID | None = None
    instructor: BaseXapiAgent | None = None
    team: BaseXapiGroup | None = None
    contextActivities: BaseXapiContextContextActivities | None = None
    revision: NonEmptyStrictStr | None = Field(
        None, examples=["revision_of_the_learning_activity"]
    )
    platform: NonEmptyStrictStr | None = Field(
        None, examples=["platform_of_the_learning_activity"]
    )
    language: LanguageTag | None = Field(None, examples=["en-US"])
    statement: BaseXapiStatementRef | None = None
    extensions: dict[IRI, str | int | bool | list | dict | None] | None = Field(
        None, examples=[{"http://example.com/extensions/example-ext": 0}]
    )

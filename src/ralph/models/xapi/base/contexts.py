"""Base xAPI `Context` definitions."""

from uuid import UUID

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .common import IRI, LanguageTag
from .groups import BaseXapiGroup
from .unnested_objects import BaseXapiActivity, BaseXapiStatementRef


class BaseXapiContextContextActivities(BaseModelWithConfig):
    """Pydantic model for context `contextActivities` property."""

    parent: BaseXapiActivity | list[BaseXapiActivity] | SkipJsonSchema[None] = Field(
        None,
        description="An Activity with a direct relation to the statement's Activity",
    )
    grouping: BaseXapiActivity | list[BaseXapiActivity] | SkipJsonSchema[None] = Field(
        None,
        description="An Activity with an indirect relation to the statement's Activity",
    )
    category: BaseXapiActivity | list[BaseXapiActivity] | SkipJsonSchema[None] = Field(
        None, description="An Activity used to categorize the Statement"
    )
    other: BaseXapiActivity | list[BaseXapiActivity] | SkipJsonSchema[None] = Field(
        None,
        description="A contextActivity that doesn't fit one of the other properties",
    )


class BaseXapiContext(BaseModelWithConfig):
    """Pydantic model for `context` property."""

    registration: UUID | SkipJsonSchema[None] = Field(
        None, description="Registration that the Statement is associated with"
    )
    instructor: BaseXapiAgent | SkipJsonSchema[None] = Field(
        None, description="Instructor that the Statement relates to"
    )
    team: BaseXapiGroup | SkipJsonSchema[None] = Field(
        None, description="Team that this Statement relates to"
    )
    contextActivities: BaseXapiContextContextActivities | SkipJsonSchema[None] = Field(
        None, description="See BaseXapiContextContextActivities"
    )
    revision: NonEmptyStrictStr | SkipJsonSchema[None] = Field(
        None,
        description="Revision of the activity associated with this Statement",
        examples=["revision_of_the_learning_activity"],
    )
    platform: NonEmptyStrictStr | SkipJsonSchema[None] = Field(
        None,
        description="Platform where the learning activity took place",
        examples=["platform_of_the_learning_activity"],
    )
    language: LanguageTag | SkipJsonSchema[None] = Field(
        None,
        description="Language in which the experience occurred",
        examples=["en-US"],
    )
    statement: BaseXapiStatementRef | SkipJsonSchema[None] = Field(
        None, description="Another Statement giving context for this Statement"
    )
    extensions: (
        dict[IRI, str | int | bool | list | dict | None] | SkipJsonSchema[None]
    ) = Field(
        None,
        description="Dictionary of other properties as needed",
        examples=[{"http://example.com/extensions/example-ext": 0}],
    )

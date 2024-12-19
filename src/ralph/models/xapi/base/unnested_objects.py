"""Base xAPI `Object` definitions (1)."""

from collections.abc import Sequence
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AnyUrl, Field, StringConstraints, field_validator

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class BaseXapiActivityDefinition(BaseModelWithConfig):
    """Pydantic model for `Activity` type `definition` property.

    Attributes:
        name (LanguageMap): Consists of the human-readable/visual name of the Activity.
        description (LanguageMap): Consists of a description of the Activity.
        type (IRI): Consists of the type of the Activity.
        moreInfo (URL): Consists of an URL to a document about the Activity.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    name: LanguageMap | None = Field(None, examples=[{"en-US": "Example course"}])
    description: LanguageMap | None = Field(
        None, examples=[{"en-US": "A fictitious example course."}]
    )
    type: IRI | None = Field(
        None, examples=["http://www.example.co.uk/types/exampleactivitytype"]
    )
    moreInfo: AnyUrl | None = Field(
        None, examples=["http://activitytype.example.com/345256"]
    )
    extensions: dict[IRI, str | int | bool | list | dict | None] | None = Field(
        None,
        examples=[
            {
                "http://example.com/activitydefinitionextensions/room": {
                    "name": "Example Room",
                    "id": "http://example.com/rooms/342",
                }
            }
        ],
    )


class BaseXapiInteractionComponent(BaseModelWithConfig):
    """Pydantic model for an interaction component.

    Attributes:
        id (str): Consists of an identifier of the interaction component.
        description (LanguageMap): Consists of the description of the interaction.
    """

    id: Annotated[str, StringConstraints(pattern=r"^[^\s]+$")]
    description: LanguageMap | None = None


class BaseXapiActivityInteractionDefinition(BaseXapiActivityDefinition):
    """Pydantic model for `Activity` type `definition` property.

    It is defined for field with interaction properties.

    Attributes:
        interactionType (str): Consists of the type of the interaction.
        correctResponsesPattern (list): Consists of a pattern for the correct response.
        choices (list): Consists of a list of selectable choices.
        scale (list): Consists of a list of the options on the `likert` scale.
        source (list): Consists of a list of sources to be matched.
        target (list): Consists of a list of targets to be matched.
        steps (list): Consists of a list of the elements making up the interaction.
    """

    interactionType: Literal[
        "true-false",
        "choice",
        "fill-in",
        "long-fill-in",
        "matching",
        "performance",
        "sequencing",
        "likert",
        "numeric",
        "other",
    ]
    correctResponsesPattern: list[NonEmptyStrictStr] | None = None
    choices: list[BaseXapiInteractionComponent] | None = None
    scale: list[BaseXapiInteractionComponent] | None = None
    source: list[BaseXapiInteractionComponent] | None = None
    target: list[BaseXapiInteractionComponent] | None = None
    steps: list[BaseXapiInteractionComponent] | None = None

    @field_validator("choices", "scale", "source", "target", "steps", mode="after")
    @classmethod
    def check_unique_ids(cls, value: Sequence[Any] | None) -> None:
        """Check the uniqueness of interaction components IDs."""
        if value and (len(value) != len({x.id for x in value if x})):
            raise ValueError("Duplicate InteractionComponents are not valid")


class BaseXapiActivity(BaseModelWithConfig):
    """Pydantic model for `Activity` type property.

    Attributes:
        id (IRI): Consists of an identifier for a single unique Activity.
        objectType (str): Consists of the value `Activity`.
        definition (dict): See BaseXapiActivityDefinition and
            BaseXapiActivityInteractionDefinition.
    """

    id: IRI = Field(examples=["http://example.adlnet.gov/xapi/example/activity"])
    objectType: Literal["Activity"] | None = None
    definition: (
        BaseXapiActivityDefinition | BaseXapiActivityInteractionDefinition | None
    ) = None


class BaseXapiStatementRef(BaseModelWithConfig):
    """Pydantic model for `StatementRef` type property.

    Attributes:
        objectType (str): Consists of the value `StatementRef`.
        id (UUID): Consists of the UUID of the referenced statement.
    """

    id: UUID
    objectType: Literal["StatementRef"]


BaseXapiUnnestedObject = BaseXapiActivity | BaseXapiStatementRef

"""Base xAPI `Statement` definitions."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .attachments import BaseXapiAttachment
from .contexts import BaseXapiContext
from .groups import BaseXapiGroup
from .objects import BaseXapiObject
from .results import BaseXapiResult
from .verbs import BaseXapiVerb


class BaseXapiStatement(BaseModelWithConfig):
    """Pydantic model for base xAPI statements."""

    id: UUID | None = Field(
        None, description="Generated UUID string from the source event string"
    )
    actor: BaseXapiAgent | BaseXapiGroup = Field(
        description="Definition of who performed the action"
    )
    verb: BaseXapiVerb = Field(description="Action between an Actor and an Activity")
    object: BaseXapiObject = Field(
        description="Definition of the thing that was acted on"
    )
    result: BaseXapiResult | None = Field(
        None, description="Outcome related to the Statement"
    )
    context: BaseXapiContext | None = Field(
        None, description="Contextual information for the Statement"
    )
    timestamp: datetime | None = Field(
        None, description="Timestamp of when the event occurred"
    )
    stored: datetime | None = Field(
        None, description="Timestamp of when the event was recorded"
    )
    authority: BaseXapiAgent | BaseXapiGroup | None = Field(
        None, description="Actor asserting this Statement is true"
    )
    version: Annotated[str, StringConstraints(pattern=r"^1\.0\.[0-9]+$")] = Field(
        "1.0.0", description="Associated xAPI version of the Statement"
    )
    attachments: list[BaseXapiAttachment] | None = Field(
        None, description="List of attachments"
    )

    @model_validator(mode="before")
    @classmethod
    def check_absence_of_empty_and_invalid_values(cls, values: Any) -> Any:
        """Check the model for empty and invalid values.

        Check that the `context` field contains `platform` and `revision` fields
        only if the `object.objectType` property is equal to `Activity`.
        """
        if isinstance(values, Sequence):
            return values

        for field, value in values.items():
            if value in [None, "", {}]:
                raise ValueError(f"{field}: invalid empty value")

            if isinstance(value, Mapping) and field != "extensions":
                cls.check_absence_of_empty_and_invalid_values(value)

        context = dict(values.get("context", {}))

        if context:
            platform = context.get("platform", {})
            revision = context.get("revision", {})
            object_type = dict(values["object"]).get("objectType", "Activity")

            if (platform or revision) and object_type != "Activity":
                raise ValueError(
                    "revision and platform properties can only be used if the "
                    "Statement's Object is an Activity"
                )

        return values

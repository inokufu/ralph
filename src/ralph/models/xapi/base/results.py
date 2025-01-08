"""Base xAPI `Result` definitions."""

from datetime import timedelta
from typing import Annotated, Any

from pydantic import Field, StrictBool, model_validator

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .common import IRI


class BaseXapiResultScore(BaseModelWithConfig):
    """Pydantic model for result `score` property."""

    scaled: Annotated[float, Field(ge=-1, le=1, strict=True)] | None = Field(
        None,
        description="Normalized score related to the experience",
        examples=[0],
    )
    raw: Annotated[float, Field(strict=True)] | None = Field(
        None, description="Non-normalized score achieved by the Actor", examples=[10]
    )
    min: Annotated[float, Field(strict=True)] | None = Field(
        None, description="Lowest possible score", examples=[0]
    )
    max: Annotated[float, Field(strict=True)] | None = Field(
        None, description="Highest possible score", examples=[20]
    )

    @model_validator(mode="after")
    def check_raw_min_max_relation(self) -> Any:
        """Check the relationship `min < raw < max`."""
        if self.min:
            if self.max and self.min > self.max:
                raise ValueError("min cannot be greater than max")
            if self.raw and self.min > self.raw:
                raise ValueError("min cannot be greater than raw")
        if self.max:
            if self.raw and self.raw > self.max:
                raise ValueError("raw cannot be greater than max")
        return self


class BaseXapiResult(BaseModelWithConfig):
    """Pydantic model for `result` property."""

    score: BaseXapiResultScore | None = Field(
        None, description="See BaseXapiResultScore"
    )
    success: StrictBool | None = Field(
        None, description="Indicates whether the attempt on the Activity was successful"
    )
    completion: StrictBool | None = Field(
        None, description="Indicates whether the Activity was completed"
    )
    response: NonEmptyStrictStr | None = Field(
        None,
        description="Response for the given Activity",
        examples=["Wow, nice work!"],
    )
    duration: timedelta | None = Field(
        None,
        description="Duration over which the Statement occurred",
        examples=["PT1234S"],
    )
    extensions: dict[IRI, str | int | bool | list | dict | None] | None = Field(
        None,
        description="Dictionary of other properties as needed",
        examples=[{"http://example.com/extensions/example-ext": 0}],
    )

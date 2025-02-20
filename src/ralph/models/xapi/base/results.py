"""Base xAPI `Result` definitions."""

from datetime import timedelta
from decimal import Decimal
from typing import Annotated, Any

from pydantic import Field, StrictBool, model_validator

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .common import IRI


class BaseXapiResultScore(BaseModelWithConfig):
    """Pydantic model for result `score` property.

    Attributes:
        scaled (Decimal): Consists of the normalized score related to the experience.
        raw (Decimal): Consists of the non-normalized score achieved by the Actor.
        min (Decimal): Consists of the lowest possible score.
        max (Decimal): Consists of the highest possible score.
    """

    scaled: Annotated[Decimal, Field(ge=-1, le=1)] | None = None
    raw: Decimal | None = None
    min: Decimal | None = None
    max: Decimal | None = None

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
    """Pydantic model for `result` property.

    Attributes:
        score (dict): See BaseXapiResultScore.
        success (bool): Indicates whether the attempt on the Activity was successful.
        completion (bool): Indicates whether the Activity was completed.
        response (str): Consists of the response for the given Activity.
        duration (timedelta): Consists of the duration over which the Statement
            occurred.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    score: BaseXapiResultScore | None = None
    success: StrictBool | None = None
    completion: StrictBool | None = None
    response: NonEmptyStrictStr | None = None
    duration: timedelta | None = None
    extensions: dict[IRI, str | int | bool | list | dict | None] | None = None

"""Base xAPI model configuration."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BaseModelWithConfig(BaseModel):
    """Pydantic model for base configuration shared among all models."""

    model_config = ConfigDict(
        extra="forbid", str_min_length=1, coerce_numbers_to_str=True, json_encoders = {Decimal: lambda v: float(v)}
    )


class BaseExtensionModelWithConfig(BaseModel):
    """Pydantic model for extension configuration shared among all models."""

    model_config = ConfigDict(
        extra="allow", str_min_length=0, coerce_numbers_to_str=True, json_encoders = {Decimal: lambda v: float(v)}
    )

"""Base xAPI `Group` definitions."""

from abc import ABC
from typing import Literal

from pydantic import Field

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .ifi import (
    BaseXapiAccountIFI,
    BaseXapiMboxIFI,
    BaseXapiMboxSha1SumIFI,
    BaseXapiOpenIdIFI,
)


class BaseXapiGroupCommonProperties(BaseModelWithConfig, ABC):
    """Pydantic model for core `Group` type property.

    It is defined for the Group which performed the action.
    """

    objectType: Literal["Group"] = Field(description="Value `Group`")
    name: NonEmptyStrictStr | None = Field(
        None, description="Full name of the Group", examples=["Team Example"]
    )


class BaseXapiAnonymousGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Anonymous Group type.
    """

    member: list[BaseXapiAgent] = Field(description="List of the members of this Group")


class BaseXapiIdentifiedGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Identified Group type.
    """

    member: list[BaseXapiAgent] | None = Field(
        None, description="List of the members of this Group"
    )


class BaseXapiIdentifiedGroupWithMbox(BaseXapiIdentifiedGroup, BaseXapiMboxIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with a mailto IFI.
    """


class BaseXapiIdentifiedGroupWithMboxSha1Sum(
    BaseXapiIdentifiedGroup, BaseXapiMboxSha1SumIFI
):
    """Pydantic model for `Group` type property.

    It is defined for group type with a hash IFI.
    """


class BaseXapiIdentifiedGroupWithOpenId(BaseXapiIdentifiedGroup, BaseXapiOpenIdIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with an openID IFI.
    """


class BaseXapiIdentifiedGroupWithAccount(BaseXapiIdentifiedGroup, BaseXapiAccountIFI):
    """Pydantic model for `Group` type property.

    It is defined for group type with an account IFI.
    """


BaseXapiGroup = (
    BaseXapiAnonymousGroup
    | BaseXapiIdentifiedGroupWithMbox
    | BaseXapiIdentifiedGroupWithMboxSha1Sum
    | BaseXapiIdentifiedGroupWithOpenId
    | BaseXapiIdentifiedGroupWithAccount
)

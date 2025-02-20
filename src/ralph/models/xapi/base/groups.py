"""Base xAPI `Group` definitions."""

from abc import ABC
from typing import Literal

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

    Attributes:
        objectType (str): Consists of the value `Group`.
        name (str): Consists of the full name of the Group.
    """

    objectType: Literal["Group"]
    name: NonEmptyStrictStr | None = None


class BaseXapiAnonymousGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Anonymous Group type.

    Attributes:
        member (list): Consist of a list of the members of this Group.
    """

    member: list[BaseXapiAgent]


class BaseXapiIdentifiedGroup(BaseXapiGroupCommonProperties):
    """Pydantic model for `Group` type property.

    It is defined for Identified Group type.

    Attributes:
        member (list): Consist of a list of the members of this Group.
    """

    member: list[BaseXapiAgent] | None = None


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

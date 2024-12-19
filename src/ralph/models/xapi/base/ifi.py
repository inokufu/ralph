"""Base xAPI `Inverse Functional Identifier` definitions."""

from typing import Annotated

from pydantic import Field, StringConstraints

from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .common import IRI, URI, MailtoEmail


class BaseXapiAccount(BaseModelWithConfig):
    """Pydantic model for IFI `account` property.

    Attributes:
        homePage (IRI): Consists of the home page of the account's service provider.
        name (str): Consists of the unique id or name of the Actor's account.
    """

    homePage: IRI = Field(examples=["http://www.example.com"])
    name: NonEmptyStrictStr = Field(examples=["John Doe"])


class BaseXapiMboxIFI(BaseModelWithConfig):
    """Pydantic model for mailto Inverse Functional Identifier.

    Attributes:
        mbox (MailtoEmail): Consists of the Agent's email address.
    """

    mbox: MailtoEmail = Field(examples=["mailto:test@example.com"])


class BaseXapiMboxSha1SumIFI(BaseModelWithConfig):
    """Pydantic model for hash Inverse Functional Identifier.

    Attributes:
        mbox_sha1sum (str): Consists of the SHA1 hash of the Agent's email address.
    """

    mbox_sha1sum: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")] = Field(
        examples=["ebd31e95054c018b10727ccffd2ef2ec3a016ee9"]
    )


class BaseXapiOpenIdIFI(BaseModelWithConfig):
    """Pydantic model for OpenID Inverse Functional Identifier.

    Attributes:
        openid (URI): Consists of an openID that uniquely identifies the Agent.
    """

    openid: URI = Field(examples=["http://johndoe.openid.example.org"])


class BaseXapiAccountIFI(BaseModelWithConfig):
    """Pydantic model for account Inverse Functional Identifier.

    Attributes:
        account (dict): See BaseXapiAccount.
    """

    account: BaseXapiAccount

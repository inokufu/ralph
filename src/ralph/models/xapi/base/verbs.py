"""Base xAPI `Verb` definitions."""

from pydantic import Field

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class BaseXapiVerb(BaseModelWithConfig):
    """Pydantic model for `verb` property.

    Attributes:
        id (IRI): Consists of an identifier for the verb.
        display (LanguageMap): Consists of a human-readable representation of the verb.
    """

    id: IRI = Field(examples=["http://adlnet.gov/expapi/verbs/attended"])
    display: LanguageMap | None = Field(
        None, examples=[{"en-GB": "attended", "en-US": "attended"}]
    )

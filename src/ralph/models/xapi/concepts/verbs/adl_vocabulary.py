"""`ADL Vocabulary` verbs definitions."""

from typing import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class AskedVerb(BaseXapiVerb):
    """Pydantic model for asked `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/asked`.
        display (dict): Consists of the dictionary `{"en-US": "asked"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/asked"] = (
        "http://adlnet.gov/expapi/verbs/asked"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["asked"]] | None = None


class AnsweredVerb(BaseXapiVerb):
    """Pydantic model for answered `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/answered`.
        display (dict): Consists of the dictionary `{"en-US": "answered"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/answered"] = (
        "http://adlnet.gov/expapi/verbs/answered"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["answered"]] | None = None


class RegisteredVerb(BaseXapiVerb):
    """Pydantic model for registered `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/registered`.
        display (dict): Consists of the dictionary `{"en-US": "registered"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/registered"] = (
        "http://adlnet.gov/expapi/verbs/registered"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["registered"]] | None = None

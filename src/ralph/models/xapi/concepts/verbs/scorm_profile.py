"""`Scorm Profile` verbs definitions."""

from typing import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class CompletedVerb(BaseXapiVerb):
    """Pydantic model for completed `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/completed`.
        display (dict): Consists of the dictionary `{"en-US": "completed"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/completed"] = (
        "http://adlnet.gov/expapi/verbs/completed"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["completed"]] | None = None


class InitializedVerb(BaseXapiVerb):
    """Pydantic model for initialized `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/initialized`.
        display (Dict): Consists of the dictionary `{"en-US": "initialized"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/initialized"] = (
        "http://adlnet.gov/expapi/verbs/initialized"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["initialized"]] | None = None


class InteractedVerb(BaseXapiVerb):
    """Pydantic model for interacted `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/interacted`.
        display (dict): Consists of the dictionary `{"en-US": "interacted"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/interacted"] = (
        "http://adlnet.gov/expapi/verbs/interacted"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["interacted"]] | None = None


class TerminatedVerb(BaseXapiVerb):
    """Pydantic model for terminated `verb`.

    Attributes:
        id (str): Consists of the value `http://adlnet.gov/expapi/verbs/terminated`.
        display (dict): Consists of the dictionary `{"en-US": "terminated"}`.
    """

    id: Literal["http://adlnet.gov/expapi/verbs/terminated"] = (
        "http://adlnet.gov/expapi/verbs/terminated"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["terminated"]] | None = None

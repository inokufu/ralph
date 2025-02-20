"""`Video` verbs definitions."""

from typing import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class PlayedVerb(BaseXapiVerb):
    """Pydantic model for played `verb`.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/played`.
        display (dict): Consists of the dictionary `{"en-US": "played"}`.
    """

    id: Literal["https://w3id.org/xapi/video/verbs/played"] = (
        "https://w3id.org/xapi/video/verbs/played"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["played"]] | None = None


class PausedVerb(BaseXapiVerb):
    """Pydantic model for paused `verb` field.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/paused`.
        display (dict): Consists of the dictionary `{"en-US": "paused"}`.
    """

    id: Literal["https://w3id.org/xapi/video/verbs/paused"] = (
        "https://w3id.org/xapi/video/verbs/paused"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["paused"]] | None = None


class SeekedVerb(BaseXapiVerb):
    """Pydantic model for seeked `verb` field.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/video/verbs/seeked`.
        display (dict): Consists of the dictionary `{"en-US": "seeked"}`.
    """

    id: Literal["https://w3id.org/xapi/video/verbs/seeked"] = (
        "https://w3id.org/xapi/video/verbs/seeked"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["seeked"]] | None = None

"""`Virtual classroom` verbs definitions."""

from typing import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class MutedVerb(BaseXapiVerb):
    """Pydantic model for muted `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/muted`.
        display (dict): Consists of the dictionary `{"en-US": "muted"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/muted"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/muted"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["muted"]] | None = None


class UnmutedVerb(BaseXapiVerb):
    """Pydantic model for unmuted `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/unmuted`.
        display (dict): Consists of the dictionary `{"en-US": "unmuted"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/unmuted"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/unmuted"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["unmuted"]] | None = None


class StartedCameraVerb(BaseXapiVerb):
    """Pydantic model for started camera `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/started-camera`.
        display (dict): Consists of the dictionary `{"en-US": "started camera"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/started-camera"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/started-camera"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["started camera"]] | None = None


class StoppedCameraVerb(BaseXapiVerb):
    """Pydantic model for stopped camera `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera`.
        display (dict): Consists of the dictionary `{"en-US": "stopped camera"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/stopped-camera"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["stopped camera"]] | None = None


class SharedScreenVerb(BaseXapiVerb):
    """Pydantic model for shared screen `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/shared-screen`.
        display (dict): Consists of the dictionary `{"en-US": "shared screen"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/shared-screen"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/shared-screen"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["shared screen"]] | None = None


class UnsharedScreenVerb(BaseXapiVerb):
    """Pydantic model for unshared screen `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen`.
        display (dict): Consists of the dictionary `{"en-US": "unshared screen"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/unshared-screen"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["unshared screen"]] | None = None


class RaisedHandVerb(BaseXapiVerb):
    """Pydantic model for raised hand `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/raised-hand`.
        display (dict): Consists of the dictionary `{"en-US": "raised hand"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/raised-hand"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["raised hand"]] | None = None


class LoweredHandVerb(BaseXapiVerb):
    """Pydantic model for lowered hand `verb`.

    Attributes:
        id (str): Consists of the value
            `https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand`.
        display (dict): Consists of the dictionary `{"en-US": "lowered hand"}`.
    """

    id: Literal["https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"] = (
        "https://w3id.org/xapi/virtual-classroom/verbs/lowered-hand"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["lowered hand"]] | None = None

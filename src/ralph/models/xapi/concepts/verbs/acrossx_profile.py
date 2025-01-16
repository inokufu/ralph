"""`AcrossX Profile` verbs definitions."""

from typing import Literal

from ...base.verbs import BaseXapiVerb
from ...constants import LANG_EN_US_DISPLAY


class PostedVerb(BaseXapiVerb):
    """Pydantic model for posted `verb`.

    Attributes:
        id (str): Consists of the value `https://w3id.org/xapi/acrossx/verbs/posted`.
        display (dict): Consists of the dictionary `{"en-US": "posted"}`.
    """

    id: Literal["https://w3id.org/xapi/acrossx/verbs/posted"] = (
        "https://w3id.org/xapi/acrossx/verbs/posted"
    )
    display: dict[Literal[LANG_EN_US_DISPLAY], Literal["posted"]] | None = None

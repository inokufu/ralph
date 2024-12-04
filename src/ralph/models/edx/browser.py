"""Browser event model definitions."""

import sys
from typing import Annotated

from pydantic import AnyUrl, StringConstraints

from .base import BaseEdxModel

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BaseBrowserModel(BaseEdxModel):
    """Pydantic model for core browser statements.

    This type of event is triggered on (XHR) POST/GET requests to the `/event` URL.

    Attributes:
        event_source (str): Consists of the value `browser`.
        page (AnyUrl): Consists of the URL (with hostname) of the visited page.
            Retrieved with:
                `window.location.href` from the JavaScript front-end.
        session (str): Consists of the md5 encrypted Django session key or an empty
            string.
    """

    event_source: Literal["browser"]
    page: AnyUrl
    session: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")] | Literal[""]

"""Base xAPI `Object` definitions (2)."""

# Nota bene: we split object definitions into `objects.py` and `unnested_objects.py`
# because of the circular dependency : objects -> context -> objects.

import sys
from datetime import datetime
from typing import Union

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .attachments import BaseXapiAttachment
from .contexts import BaseXapiContext
from .groups import BaseXapiGroup
from .results import BaseXapiResult
from .unnested_objects import BaseXapiUnnestedObject
from .verbs import BaseXapiVerb

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


class BaseXapiSubStatement(BaseModelWithConfig):
    """Pydantic model for `SubStatement` type property.

    Attributes:
        actor (dict): See BaseXapiAgent and BaseXapiGroup.
        verb (dict): See BaseXapiVerb.
        object (dict): See BaseXapiUnnestedObject.
        objectType (dict): Consists of the value `SubStatement`.
    """

    actor: BaseXapiAgent | BaseXapiGroup
    verb: BaseXapiVerb
    object: BaseXapiUnnestedObject
    objectType: Literal["SubStatement"]
    result: BaseXapiResult | None = None
    context: BaseXapiContext | None = None
    timestamp: datetime | None = None
    attachments: list[BaseXapiAttachment] | None = None


BaseXapiObject = Union[
    BaseXapiUnnestedObject,
    BaseXapiSubStatement,
    BaseXapiAgent,
    BaseXapiGroup,
]

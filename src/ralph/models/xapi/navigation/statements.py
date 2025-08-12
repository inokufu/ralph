"""Navigation xAPI event definitions."""

from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.activity_streams_vocabulary import PageActivity
from ..concepts.verbs.scorm_profile import TerminatedVerb
from ..concepts.verbs.tincan_vocabulary import ViewedVerb


class PageViewed(BaseXapiStatement):
    """Pydantic model for page viewed statement.

    Example: John viewed the https://www.fun-mooc.fr/ page.

    Attributes:
       object (dict): See PageActivity.
       verb (dict): See ViewedVerb.
    """

    object: PageActivity
    verb: ViewedVerb = ViewedVerb()


class PageTerminated(BaseXapiStatement):
    """Pydantic model for page terminated statement.

    Example: John terminated the https://www.fun-mooc.fr/ page.

    Attributes:
       object (dict): See PageActivity.
       verb (dict): See TerminatedVerb.
    """

    object: PageActivity
    verb: TerminatedVerb = TerminatedVerb()

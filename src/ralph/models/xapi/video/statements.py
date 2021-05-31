"""Video xAPI event definitions"""

from ..base import BaseXapiModel
from .fields.contexts import VideoPlayedContextField
from .fields.objects import VideoObjectField
from .fields.results import VideoPlayedResultField
from .fields.verbs import VideoPlayedVerbField


class VideoPlayed(BaseXapiModel):
    """Represents a video played xAPI statement.

    WARNING: This model is based on the video played xAPI event generated by `marsha`.

    Attributes:
        object (VideoObjectField): See VideoObjectField.
        verb (VideoPlayedVerbField): See VideoPlayedVerbField.
        result (VideoPlayedResultField): See VideoPlayedResultField.
        context (VideoPlayedContextField): See VideoPlayedContextField.
    """

    object: VideoObjectField
    verb: VideoPlayedVerbField
    result: VideoPlayedResultField
    context: VideoPlayedContextField
"""Video event model definitions."""

from typing import Literal

from pydantic import Json

from ralph.models.edx.video.fields.events import (
    PauseVideoEventField,
    PlayVideoEventField,
    SeekVideoEventField,
    SpeedChangeVideoEventField,
    StopVideoEventField,
    VideoBaseEventField,
    VideoHideTranscriptEventField,
    VideoShowTranscriptEventField,
)
from ralph.models.selector import selector

from ..browser import BaseBrowserModel


class UILoadVideo(BaseBrowserModel):
    """Pydantic model for `load_video` statement.

    The browser emits this statement when the video is fully rendered and ready to
    play.

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `load_video`.
        name (str): Consists either of the value `load_video` or `edx.video.loaded`.
    """

    __selector__ = selector(event_source="browser", event_type="load_video")

    event: Json[VideoBaseEventField] | VideoBaseEventField
    event_type: Literal["load_video"]
    name: Literal["load_video", "edx.video.loaded"]


class UIPlayVideo(BaseBrowserModel):
    """Pydantic model for `play_video` statement.

    The browser emits this statement when a user selects the video player's play
    control.

    Attributes:
        event (PlayVideoEventField): See PlayVideoEventField.
        event_type (str): Consists of the value `play_video`.
        name (str): Consists either of the value `play_video` or `edx.video.played`.
    """

    __selector__ = selector(event_source="browser", event_type="play_video")

    event: Json[PlayVideoEventField] | PlayVideoEventField
    event_type: Literal["play_video"]
    name: Literal["play_video", "edx.video.played"] | None = None


class UIPauseVideo(BaseBrowserModel):
    """Pydantic model for `pause_video` statement.

    The browser emits this statement when a user selects the video player's pause
    control.

    Attributes:
        event (PauseVideoEventField): See PauseVideoEventField.
        event_type (str): Consists of the value `pause_video`.
        name (str): Consists either of the value `pause_video` or `edx.video.paused`.
    """

    __selector__ = selector(event_source="browser", event_type="pause_video")

    event: Json[PauseVideoEventField] | PauseVideoEventField
    event_type: Literal["pause_video"]
    name: Literal["pause_video", "edx.video.paused"] | None = None


class UISeekVideo(BaseBrowserModel):
    """Pydantic model for `seek_video` statement.

    The browser emits this statement when a user selects a user interface control to go
    to a different point in the video file.

    Attributes:
        event (SeekVideoEventField): See SeekVideoEventField.
        event_type (str): Consists of the value `seek_video`.
        name (str): Consists either of the value `seek_video` or
            `edx.video.position.changed`.
    """

    __selector__ = selector(event_source="browser", event_type="seek_video")

    event: Json[SeekVideoEventField] | SeekVideoEventField
    event_type: Literal["seek_video"]
    name: Literal["seek_video", "edx.video.position.changed"] | None = None


class UIStopVideo(BaseBrowserModel):
    """Pydantic model for `stop_video` statement.

    The browser emits this statement when the video player reaches the end of the video
    file and play automatically stops.

    Attributes:
        event (StopVideoEventField): See StopVideoEventField.
        event_type (str): Consists of the value `stop_video`.
        name (str): Consists either of the value `stop_video` or `edx.video.stopped`.
    """

    __selector__ = selector(event_source="browser", event_type="stop_video")

    event: Json[StopVideoEventField] | StopVideoEventField
    event_type: Literal["stop_video"]
    name: Literal["stop_video", "edx.video.stopped"] | None = None


class UIHideTranscript(BaseBrowserModel):
    """Pydantic model for `hide_transcript` statement.

    The browser emits this statement when a user selects <kbd>CC</kbd> to suppress
    display of the video transcript.

    Attributes:
        event (VideoTranscriptEventField): See VideoTranscriptEventField.
        event_type (str): Consists of the value `hide_transcript`.
        name (str): Consists either of the value `hide_transcript` or
            `edx.video.transcript.hidden`.
    """

    __selector__ = selector(event_source="browser", event_type="hide_transcript")

    event: Json[VideoHideTranscriptEventField] | VideoHideTranscriptEventField
    event_type: Literal["hide_transcript"]
    name: Literal["hide_transcript", "edx.video.transcript.hidden"]


class UIShowTranscript(BaseBrowserModel):
    """Pydantic model for `show_transcript` statement.

    The browser emits this statement when a user selects <kbd>CC</kbd> to display the
    video transcript.

    Attributes:
        event (VideoTranscriptEventField): See VideoTranscriptEventField.
        event_type (str): Consists of the value `show_transcript`.
        name (str): Consists either of the value `show_transcript` or
            `edx.video.transcript.shown`.
    """

    __selector__ = selector(event_source="browser", event_type="show_transcript")

    event: Json[VideoShowTranscriptEventField] | VideoShowTranscriptEventField
    event_type: Literal["show_transcript"]
    name: Literal["show_transcript", "edx.video.transcript.shown"]


class UISpeedChangeVideo(BaseBrowserModel):
    """Pydantic model for `speed_change_video` statement.

    The browser emits this statement when a user selects a different playing speed for
    the video.

    Attributes:
        event (SpeedChangeVideoEventField): See SpeedChangeVideoEventField.
        event_type (str): Consists of the value `speed_change_video`.
    """

    __selector__ = selector(event_source="browser", event_type="speed_change_video")

    event: Json[SpeedChangeVideoEventField] | SpeedChangeVideoEventField
    event_type: Literal["speed_change_video"]
    name: Literal["speed_change_video"] | None = None


class UIVideoHideCCMenu(BaseBrowserModel):
    """Pydantic model for `video_hide_cc_menu` statement.

    The browser emits this statement when a user selects a language from the CC menu
    for a video that has transcripts in multiple languages

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `video_hide_cc_menu`.
    """

    __selector__ = selector(event_source="browser", event_type="video_hide_cc_menu")

    event: Json[VideoBaseEventField] | VideoBaseEventField
    event_type: Literal["video_hide_cc_menu"]
    name: Literal["video_hide_cc_menu"] | None = None


class UIVideoShowCCMenu(BaseBrowserModel):
    """Pydantic model for `video_show_cc_menu` statement.

    The browser emits this statement when a user selects CC for a video that has
    transcripts in multiple languages.

    Note: This statement is emitted in addition to the show_transcript event.

    Attributes:
        event (VideoBaseEventField): See VideoBaseEventField.
        event_type (str): Consists of the value `video_show_cc_menu`.
    """

    __selector__ = selector(event_source="browser", event_type="video_show_cc_menu")

    event: Json[VideoBaseEventField] | VideoBaseEventField
    event_type: Literal["video_show_cc_menu"]
    name: Literal["video_show_cc_menu"] | None = None

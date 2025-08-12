"""LMS xAPI event definitions."""

from datetime import datetime

from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.audio import AudioActivity
from ..concepts.activity_types.scorm_profile import CourseActivity
from ..concepts.activity_types.tincan_vocabulary import DocumentActivity
from ..concepts.activity_types.video import VideoActivity
from ..concepts.verbs.adl_vocabulary import RegisteredVerb
from ..concepts.verbs.navy_common_reference_profile import AccessedVerb, UploadedVerb
from ..concepts.verbs.tincan_vocabulary import DownloadedVerb, UnregisteredVerb
from .contexts import (
    LMSCommonContext,
    LMSContext,
    LMSDownloadedAudioContext,
    LMSDownloadedVideoContext,
    LMSRegistrationContext,
)
from .objects import LMSFileObject, LMSPageObject


class BaseLMSStatement(BaseXapiStatement):
    """Pydantic model for LMS core statements.

    Attributes:
        timestamp (datetime): Timestamp of when the event occurred.
    """

    timestamp: datetime
    context: LMSContext


# Course registration
class LMSRegisteredCourse(BaseLMSStatement):
    """Pydantic model for LMS `registered to a course` statement.

    Example: John is registered to a course.

    Attributes:
        verb (dict): See RegisteredVerb.
        object (dict): See CourseActivity.
        context (dict): See LMSRegistrationContext.
    """

    verb: RegisteredVerb = RegisteredVerb()
    object: CourseActivity
    context: LMSRegistrationContext


class LMSUnregisteredCourse(BaseLMSStatement):
    """Pydantic model for LMS `unregistered to a course` statement.

    Example: John is unregistered to a course.

    Attributes:
        verb (dict): See UnregisteredVerb.
        object (dict): See CourseActivity.
        context (dict): See LMSRegistrationContext.
    """

    verb: UnregisteredVerb = UnregisteredVerb()
    object: CourseActivity
    context: LMSRegistrationContext


# Page
class LMSAccessedPage(BaseLMSStatement):
    """Pydantic model for LMS `accessed a page` statement.

    Example: John has accessed a page of an LMS or a website.

    Attributes:
        verb (dict): See AccessedVerb.
        object (dict): See LMSPageObject.
    """

    verb: AccessedVerb = AccessedVerb()
    object: LMSPageObject


# File
class LMSAccessedFile(BaseLMSStatement):
    """Pydantic model for LMS `accessed a file` statement.

    Example: John has accessed a file such as a pdf, doc, txt, ppt, xls, csv, etc...

    Attributes:
        verb (dict): See AccessedVerb.
        object (dict): See LMSFileObject.
    """

    verb: AccessedVerb = AccessedVerb()
    object: LMSFileObject


class LMSUploadedFile(BaseLMSStatement):
    """Pydantic model for LMS `uploaded a file` statement.

    Example: John has uploaded a file such as a pdf, doc, txt, ppt, xls, csv, etc...

    Attributes:
        verb (dict): See UploadedVerb.
        object (dict): See LMSFileObject.
        context (dict) See LMSCommonContext.
    """

    verb: UploadedVerb = UploadedVerb()
    object: LMSFileObject
    context: LMSCommonContext


class LMSDownloadedFile(BaseLMSStatement):
    """Pydantic model for LMS `downloaded a file` statement.

    Example: John has uploaded a file such as a pdf, doc, txt, ppt, xls, csv, etc...

    Attributes:
        verb (dict): See DownloadedVerb.
        object (dict): See LMSFileObject.
        context (dict): see LMSCommonContext.
    """

    verb: DownloadedVerb = DownloadedVerb()
    object: LMSFileObject
    context: LMSCommonContext


# Video
class LMSUploadedVideo(BaseLMSStatement):
    """Pydantic model for LMS `uploaded a video` statement.

    Example: John uploaded a video.

    Attributes:
        verb (dict): See UploadedVerb.
        object (dict): See VideoActivity.
        context (dict): see LMSCommonContext.
    """

    object: VideoActivity
    verb: UploadedVerb = UploadedVerb()
    context: LMSCommonContext


class LMSDownloadedVideo(BaseLMSStatement):
    """Pydantic model for LMS `downloaded a video` statement.

    Example: John downloaded (rather than played) a video.

    Attributes:
        verb (dict): See DownloadedVerb.
        object (dict): See VideoActivity.
        context (dict): See LMSDownloadedVideoContext.
    """

    object: VideoActivity
    verb: DownloadedVerb = DownloadedVerb()
    context: LMSDownloadedVideoContext


# Document
class LMSUploadedDocument(BaseLMSStatement):
    """Pydantic model for LMS `uploaded a document` statement.

    Example: John uploaded a document.

    Attributes:
        verb (dict): See UploadedVerb.
        object (dict): See DocumentActivity.
        context (dict): see LMSCommonContext.
    """

    object: DocumentActivity
    verb: UploadedVerb = UploadedVerb()
    context: LMSCommonContext


class LMSDownloadedDocument(BaseLMSStatement):
    """Pydantic model for LMS `downloaded a document` statement.

    Example: John downloaded (rather than accessed or opened) a document.

    Attributes:
        verb (dict): See DownloadedVerb.
        object (dict): See DocumentActivity.
        context (dict): see LMSCommonContext.
    """

    object: DocumentActivity
    verb: DownloadedVerb = DownloadedVerb()
    context: LMSCommonContext


# Audio
class LMSUploadedAudio(BaseLMSStatement):
    """Pydantic model for LMS `uploaded an audio` statement.

    Example: John uploaded an audio.

    Attributes:
        verb (dict): See UploadedVerb.
        object (dict): See AudioActivity.
        context (dict): see LMSCommonContext.
    """

    object: AudioActivity
    verb: UploadedVerb = UploadedVerb()
    context: LMSCommonContext


class LMSDownloadedAudio(BaseLMSStatement):
    """Pydantic model for LMS `downloaded an audio` statement.

    Example: John downloaded (rather than played) an audio.

    Attributes:
        verb (dict): See DownloadedVerb.
        object (dict): See AudioActivity.
        context (dict): see LMSDownloadedAudioContext.
    """

    object: AudioActivity
    verb: DownloadedVerb = DownloadedVerb()
    context: LMSDownloadedAudioContext

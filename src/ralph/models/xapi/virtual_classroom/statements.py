"""Virtual classroom xAPI event definitions."""

from datetime import datetime

from ..base.statements import BaseXapiStatement
from ..concepts.activity_types.acrossx_profile import MessageActivity
from ..concepts.activity_types.scorm_profile import CMIInteractionActivity
from ..concepts.activity_types.virtual_classroom import VirtualClassroomActivity
from ..concepts.verbs.acrossx_profile import PostedVerb
from ..concepts.verbs.activity_streams_vocabulary import JoinVerb, LeaveVerb
from ..concepts.verbs.adl_vocabulary import AnsweredVerb, AskedVerb
from ..concepts.verbs.scorm_profile import InitializedVerb, TerminatedVerb
from ..concepts.verbs.virtual_classroom import (
    LoweredHandVerb,
    MutedVerb,
    RaisedHandVerb,
    SharedScreenVerb,
    StartedCameraVerb,
    StoppedCameraVerb,
    UnmutedVerb,
    UnsharedScreenVerb,
)
from .contexts import (
    VirtualClassroomAnsweredPollContext,
    VirtualClassroomContext,
    VirtualClassroomInitializedContext,
    VirtualClassroomJoinedContext,
    VirtualClassroomPostedPublicMessageContext,
    VirtualClassroomStartedPollContext,
    VirtualClassroomTerminatedContext,
)
from .results import VirtualClassroomAnsweredPollResult


class BaseVirtualClassroomStatement(BaseXapiStatement):
    """Pydantic model for Virtual Classroom core statements.

    Attributes:
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    timestamp: datetime


# Mandatory statements


class VirtualClassroomInitialized(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom initialized statement.

    Example: John has entered the virtual classroom as the first user.

    Attributes:
        verb (dict): See InitializedVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomInitializedContext.
    """

    verb: InitializedVerb = InitializedVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomInitializedContext


class VirtualClassroomJoined(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom joined statement.

    Example: Jane has entered the virtual classroom.

    Attributes:
        verb (dict): See JoinVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomJoinedContext.
    """

    verb: JoinVerb = JoinVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomJoinedContext


class VirtualClassroomLeft(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom joined statement.

    Example: Jane has left the virtual classroom.

    Attributes:
        verb (dict): See LeaveVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomContext.

    """

    verb: LeaveVerb = LeaveVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomTerminated(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom terminated statement.

    Example: Jane has terminated the virtual classroom.

    Attributes:
        verb (dict): See TerminatedVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomTerminatedContext.

    """

    verb: TerminatedVerb = TerminatedVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomTerminatedContext


# Recommended statements


class VirtualClassroomMuted(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom muted statement.

    Example: Jane has muted herself or has been muted.

    Attributes:
        verb (dict): See MutedVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomMutedContext.

    """

    verb: MutedVerb = MutedVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomUnmuted(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom unmuted statement.

    Example: Jane has unmuted herself or has been unmuted.

    Attributes:
        verb (dict): See UnmutedVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomContext.

    """

    verb: UnmutedVerb = UnmutedVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomStartedCamera(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom started camera statement.

    Example: Jane has started her camera.

    Attributes:
        verb (dict): See StartedCameraVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomContext.

    """

    verb: StartedCameraVerb = StartedCameraVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomStoppedCamera(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom stopped camera statement.

    Example: Jane has stopped her camera.

    Attributes:
        verb (dict): See StoppedCameraVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomStoppedCameraContext.

    """

    verb: StoppedCameraVerb = StoppedCameraVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomSharedScreen(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom shared screen statement.

    Example: Jane has shared her screen.

    Attributes:
        verb (dict): See SharedScreenVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomSharedScreenContext.

    """

    verb: SharedScreenVerb = SharedScreenVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomUnsharedScreen(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom unshared screen statement.

    Example: Jane has unshared her screen or her screen has been unshared by the
    moderator.

    Attributes:
        verb (dict): See UnsharedScreenVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomUnsharedScreenContext.

    """

    verb: UnsharedScreenVerb = UnsharedScreenVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomRaisedHand(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom raised hand statement.

    Example: Jane has raised the hand.

    Attributes:
        verb (dict): See RaisedHandVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomRaisedHandContext.

    """

    verb: RaisedHandVerb = RaisedHandVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomLoweredHand(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom lowered hand statement.

    Example: Jane has lowered the hand.

    Attributes:
        verb (dict): See LoweredHandVerb.
        object (dict): See VirtualClassroomActivity.
        context (dict): See VirtualClassroomLoweredHandContext.

    """

    verb: LoweredHandVerb = LoweredHandVerb()
    object: VirtualClassroomActivity
    context: VirtualClassroomContext


class VirtualClassroomStartedPoll(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom started poll statement.

    Example: A poll has been started in the virtual classroom in order
    to collect participants opinions about a given question.

    Attributes:
        verb (dict): See AskedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See VirtualClassroomLoweredHandContext.

    """

    verb: AskedVerb = AskedVerb()
    object: CMIInteractionActivity
    context: VirtualClassroomStartedPollContext


class VirtualClassroomAnsweredPoll(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom answered poll statement.

    Example: John answered to a poll question.

    Attributes:
        verb (dict): See AskedVerb.
        object (dict): See CMIInteractionActivity.
        context (dict): See VirtualClassroomAnsweredPollContext.
        result (dict): See AnsweredPollResult.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
        result (dict): See AnsweredPollResult.
        timestamp (datetime): Consists of the timestamp of when the event occurred.
    """

    verb: AnsweredVerb = AnsweredVerb()
    object: CMIInteractionActivity
    context: VirtualClassroomAnsweredPollContext
    result: VirtualClassroomAnsweredPollResult


class VirtualClassroomPostedPublicMessage(BaseVirtualClassroomStatement):
    """Pydantic model for virtual classroom posted public message statement.

    Example: John sent a message in the public chat.

    Attributes:
        verb (dict): See PostedVerb.
        object (dict): See MessageActivity.
        context (dict): See VirtualClassroomPostedPublicMessageContext.

    """

    verb: PostedVerb = PostedVerb()
    object: MessageActivity
    context: VirtualClassroomPostedPublicMessageContext

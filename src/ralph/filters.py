"""Ralph tracking logs filters."""

from collections.abc import Mapping
from typing import Any

from .exceptions import EventKeyError


def anonymous(event: Mapping) -> Any:
    """Remove anonymous events.

    Args:
        event (dict): Event to filter.

    Returns:
        event (dict): When event is not anonymous.
        None: Otherwise.

    Raises:
        EventKeyError: When the event does not contain the `username` key.

    """
    if "username" not in event:
        raise EventKeyError("Cannot filter anonymous event without 'username' key.")
    if not event.get("username", ""):
        return None

    return event

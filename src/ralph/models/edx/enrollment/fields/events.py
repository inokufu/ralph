"""Enrollment models event field definition."""

from typing import Literal

from ...base import AbstractBaseEventField


class EnrollmentEventField(AbstractBaseEventField):
    """Pydantic model for enrollment `event` field.

    Note: Only server enrollment statements require an `event` field.

    Attributes:
        course_id (str): Consists in the course in which the student was enrolled or
            unenrolled.
        mode (str): Takes either `audit`, `honor`, `professional` or `verified` value.
            It identifies the student’s enrollment mode.
        user_id (int): Identifies the student who was enrolled or unenrolled.
    """

    course_id: str
    mode: Literal["audit", "honor", "professional", "verified"]
    user_id: int | Literal[""] | None = None

"""Enrollment event models context fields definitions."""

from typing import Literal

from ...base import BaseContextField


class EdxCourseEnrollmentUpgradeClickedContextField(BaseContextField):
    """Pydantic model for `edx.course.enrollment.upgrade_clicked`.`context` field.

    In addition to the common context member fields, this statement also comprises the
    `mode` context member field.

    Attributes:
        mode (str): Consists of either the `audit` or `honor` value. It identifies the
            enrollment mode when the user clicked <kbd>Challenge Yourself</kbd>.
    """

    mode: Literal["audit", "honor"]


class EdxCourseEnrollmentUpgradeSucceededContextField(BaseContextField):
    """Pydantic model for `edx.course.enrollment.upgrade.succeeded`.`context` field.

    In addition to the common context member fields, this statement also comprises the
    `mode` context member field.

    Attributes:
        mode (str): Consists of the `verified` value.
    """

    mode: Literal["verified"]

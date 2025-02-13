"""CozyStack exceptions for Ralph."""

import logging

logger = logging.getLogger(__name__)


class CozyStackError(Exception):
    """Base class for CozyStack exceptions."""

    message = ""

    def __init__(self, message: str | None = None):
        """Init CozyStackError."""
        super().__init__(message if message else self.message)


# --- 400 --- #


class InvalidRequestError(CozyStackError):
    """Base class for CozyStack 400 bad request exceptions."""

    message = "Invalid request"


class ExpiredTokenError(InvalidRequestError):
    """Raised when authentication token has expired and must be renew."""

    message = "Authentication token has expired"


# --- 403 errors --- #


class ForbiddenError(CozyStackError):
    """Raised when user has insufficient permissions to operate on doctype."""

    message = "Insufficient permissions"


# --- 404 errors --- #


class NotFoundError(CozyStackError):
    """Base class for CozyStack 404 not found exceptions."""

    message = "Resource not found"


class DatabaseDoesNotExistError(NotFoundError):
    """Raised when doctype does not exist."""

    message = "Database does not exist"


# --- 500 errors --- #


class ExecutionError(CozyStackError):
    """Internal server error exception."""

    message = "Internal server error"

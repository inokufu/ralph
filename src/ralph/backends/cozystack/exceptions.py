"""CozyStack exceptions for Ralph."""

import logging

import httpx
from fastapi import status
from httpx import Response

logger = logging.getLogger(__name__)


class CozyStackError(Exception):
    """Base class for CozyStack exceptions."""

    message = ""

    def __init__(self):
        """Init CozyStackError."""
        super().__init__(self.message)


# --- 400 --- #


class InvalidRequestError(CozyStackError):
    """Base class for CozyStack 400 bad request exceptions."""

    message = "Invalid request"


class ExpiredTokenError(InvalidRequestError):
    """Raised when authentication token has expired and must be renew."""

    message = "Authentication token has expired"


class QueryFailedError(InvalidRequestError):
    """Raised when query could not be executed."""

    message = "Query has failed"


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


def check_cozystack_error(response: Response):
    """Check if response contains error and raise the proper exception."""
    try:
        response.raise_for_status()
    except httpx.HTTPError as exc:
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if response.json() == {"error": "code=400, message=Expired token"}:
                raise ExpiredTokenError() from exc

            elif response.json() == {"detail": "xAPI statements query failed"}:
                raise QueryFailedError() from exc

            raise InvalidRequestError() from exc

        elif response.status_code == status.HTTP_403_FORBIDDEN:
            raise ForbiddenError() from exc

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            if response.json().get("reason", "") == "Database does not exist.":
                raise DatabaseDoesNotExistError() from exc

            raise NotFoundError() from exc

        elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise ExecutionError() from exc

        raise CozyStackError() from exc

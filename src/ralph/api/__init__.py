"""Main module for Ralph's LRS API."""

import os
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import urlparse

import sentry_sdk
from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from ralph.conf import settings

from .. import __version__
from .auth import get_authenticated_user
from .auth.user import AuthenticatedUser
from .routers import health, statements, xapi


@lru_cache(maxsize=None)
def get_health_check_routes() -> list:
    """Return the health check routes."""
    return [route.path for route in health.router.routes]


def filter_transactions(event: Mapping, hint) -> dict | None:  # noqa: ARG001
    """Filter transactions for Sentry."""
    url = urlparse(event["request"]["url"])

    if settings.SENTRY_IGNORE_HEALTH_CHECKS and url.path in get_health_check_routes():
        return None

    return event


if settings.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_LRS_TRACES_SAMPLE_RATE,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
        before_send_transaction=filter_transactions,
    )

app = FastAPI()
app.include_router(statements.router)
app.include_router(health.router)
app.include_router(xapi.router)


@app.get("/whoami")
async def whoami(
    user: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
) -> dict[str, Any]:
    """Return the current user's username along with their scopes."""
    return {
        "agent": user.agent.model_dump(mode="json", exclude_none=True),
        "scopes": user.scopes,
    }


@app.middleware("http")
async def check_x_experience_api_version_header(
    request: Request, call_next: Callable[[Request], Response]
) -> Response:
    """Check the headers for the X-Experience-API-Version in every request."""
    # about resource doesn't need the "X-Experience-API-Version" header
    if request.url.path.startswith(
        settings.XAPI_PREFIX
    ) and request.url.path != os.path.join(settings.XAPI_PREFIX, "about"):
        # check that request includes X-Experience-API-Version header
        if "X-Experience-API-Version" not in request.headers:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing X-Experience-API-Version header"},
            )

        # check that given X-Experience-API-Version is valid
        if (
            request.headers["X-Experience-API-Version"]
            not in settings.XAPI_VERSIONS_SUPPORTED
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid X-Experience-API-Version header"},
            )

    return await call_next(request)


@app.middleware("http")
async def set_x_experience_api_version_header(
    request: Request, call_next: Callable[[Request], Response]
) -> Response:
    """Set X-Experience-API-Version header in every response."""
    response = await call_next(request)

    if (
        request.headers.get("X-Experience-API-Version")
        in settings.XAPI_VERSIONS_SUPPORTED
    ):
        response.headers["X-Experience-API-Version"] = request.headers[
            "X-Experience-API-Version"
        ]
    else:
        response.headers["X-Experience-API-Version"] = settings.XAPI_VERSION_FALLBACK

    return response


@app.middleware("http")
async def set_x_experience_api_consistent_through_header(
    request: Request, call_next: Callable[[Request], Response]
) -> Response:
    """Set X-Experience-API-Version header in every response."""
    response = await call_next(request)

    # this arbitrary value is based on
    # https://github.com/adlnet/ADL_LRS/blob/master/lrs/utils/XAPIConsistentThroughMiddleware.py#L16
    time = datetime.now(tz=timezone.utc) - timedelta(seconds=3)
    response.headers["X-Experience-API-Consistent-Through"] = time.isoformat()
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Called on invalid request data, return error detail as json response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(
    _: Request, exc: ValidationError  # noqa: ARG001
) -> JSONResponse:
    """Called on parameter validation error, return generic error message."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "An unexpected validation error has occurred."},
    )

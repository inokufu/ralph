"""Cozy authentication tool for the Ralph API."""

import logging
import re
from collections.abc import Mapping
from typing import Annotated

import httpx
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import ValidationError

from ralph.api.auth.token import BaseIDToken
from ralph.api.auth.user import AuthenticatedUser
from ralph.backends.cozystack.client import CozyStackHttpClient
from ralph.conf import AuthBackend, settings
from ralph.models.cozy import CozyAuthData

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(
    name="X-Auth-Token", scheme_name="Cozy Authentication", auto_error=False
)

unauthorized_http_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class CozyIDToken(BaseIDToken):
    """Pydantic model representing the core of Cozy ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str): Audience(s) that this ID Token is intended for.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements.
        session_id (str): CozyStack session identifier.
    """

    sub: str | None = None
    aud: list[str]
    session_id: str | None = None


def decode_auth_token(x_auth_token: str) -> dict:
    """Decode Cozy ID token (jwt).

    Attributes:
        x_auth_token (str): Cozy authentication token (jwt).

    Return:
        Dict: Decoded token.

    Raises:
        HTTPException: When decoding fails.
    """
    try:
        if not isinstance(x_auth_token, str):
            raise ValueError("X-Auth-Token must be a string")

        x_auth_token_splits = x_auth_token.split(" ")

        if (
            len(x_auth_token_splits) != 2  # noqa: PLR2004
            or x_auth_token_splits[0] != "Bearer"
        ):
            raise ValueError("X-Auth-Token must be a Bearer token")

        _, encoded_token = x_auth_token_splits

        return jwt.decode(
            encoded_token,
            key=None,
            options={"verify_signature": False, "verify_aud": False},
        )
    except (ValueError, ExpiredSignatureError, JWTError, JWTClaimsError) as exc:
        logger.error("Unable to decode the ID token: %s", exc)
        raise unauthorized_http_exception from exc


def model_validate_cozy_id_token(decoded_token: Mapping) -> CozyIDToken:
    """Validate decoded authentication token data.

    Attributes:
        decoded_token (dict): Cozy decoded token.

    Return:
        CozyIDToken: Decoded authentication token data.

    Raises:
        HTTPException: When data validation fails.
    """
    try:
        return CozyIDToken.model_validate(decoded_token)
    except ValidationError as exc:
        logger.error("Unable to validate the ID token: %s", exc)
        raise unauthorized_http_exception from exc


def validate_auth_against_cozystack(
    id_token: CozyIDToken, x_auth_token: str
) -> CozyAuthData:
    """Validate Cozy ID token against Cozy-Stack server.

    Attributes:
        id_token (CozyIDToken): Decoded authentication token data.
        x_auth_token (str): Cozy authentication token (jwt).

    Return:
        CozyAuthData: Cozy authentication data required to request CozyStack.

    Raises:
        HTTPException: When validation against Cozy-Stack fails.
    """
    instance_url = id_token.iss

    if not re.search("^http(?:s)?://", instance_url):
        instance_url = "http://" + instance_url

    cozy_auth_data = CozyAuthData(instance_url=instance_url, token=x_auth_token)

    # request cozy-stack to check auth is valid
    try:
        with CozyStackHttpClient(target=cozy_auth_data.model_dump_json()) as client:
            response = client.get("/_all_doctypes")
            response.raise_for_status()

    except httpx.HTTPError as exc:
        logger.error(
            f"Unable to authenticate user against cozy-stack ({instance_url}): %s", exc
        )
        raise unauthorized_http_exception from exc

    return cozy_auth_data


def get_cozy_user(
    x_auth_token: Annotated[str | None, Security(api_key_header)]
) -> AuthenticatedUser | None:
    """Decode and validate Cozy ID token against Cozy-Stack server.

    Attributes:
        x_auth_token (str): Cozy authentication token (jwt).

    Return:
        AuthenticatedUser (AuthenticatedUser)

    Raises:
        HTTPException
    """
    if AuthBackend.COZY not in settings.RUNSERVER_AUTH_BACKENDS:
        return None

    if x_auth_token is None or "Bearer" not in x_auth_token:
        logger.debug("Not using cozy auth which requires a Bearer token")
        return None

    decoded_token = decode_auth_token(x_auth_token)
    id_token = model_validate_cozy_id_token(decoded_token)
    cozy_auth_data = validate_auth_against_cozystack(id_token, x_auth_token)

    user = AuthenticatedUser(
        agent={"openid": f"{id_token.iss}/{id_token.sub or "cli"}"},
        scopes=["statements/write", "statements/read/mine"],
        target=cozy_auth_data.model_dump_json(),
    )

    return user

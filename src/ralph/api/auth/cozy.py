"""Cozy authentication tool for the Ralph API."""

import logging
import os
from typing import Dict, List, Optional

import httpx
from fastapi import Header, HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import ValidationError
from typing_extensions import Annotated

from ralph.api.auth.token import BaseIDToken
from ralph.api.auth.user import AuthenticatedUser
from ralph.models.cozy import CozyAuthData

logger = logging.getLogger(__name__)

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
        session_id (int): CozyStack session identifier.
    """

    sub: Optional[str] = None
    aud: List[str]


def decode_auth_token(x_auth_token: str) -> Dict:
    """Decode Cozy ID token (jwt).

    Attributes:
        x_auth_token (str): Cozy authentication token (jwt).

    Return:
        Dict: Decoded token.
    """
    try:
        _, encoded_token = x_auth_token.split(" ")

        return jwt.decode(
            encoded_token,
            key=None,
            options={"verify_signature": False, "verify_aud": False},
        )
    except (ValueError, ExpiredSignatureError, JWTError, JWTClaimsError) as exc:
        logger.error("Unable to decode the ID token: %s", exc)
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
        HTTPException: When validation fails.
    """
    instance_url = id_token.iss

    if not instance_url.startswith("http://"):
        instance_url = "http://" + instance_url

    # request cozy-stack to check auth is valid
    try:
        response = httpx.get(
            os.path.join(instance_url, "data", "_all_doctypes"),
            headers={"Accept": "application/json", "Authorization": x_auth_token},
        )

        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Unable to authenticate user against cozy-stack: %s", exc)
        raise unauthorized_http_exception from exc

    return CozyAuthData(instance_url=instance_url, token=x_auth_token)


def get_cozy_user(
    x_auth_token: Annotated[str | None, Header()] = None
) -> AuthenticatedUser:
    """Decode and validate Cozy ID token against Cozy-Stack server.

    Attributes:
        x_auth_token (str): Cozy authentication token (jwt).

    Return:
        AuthenticatedUser (AuthenticatedUser)

    Raises:
        HTTPException
    """
    if x_auth_token is None or "Bearer" not in x_auth_token:
        logger.debug("Not using cozy auth which requires a Bearer token")
        return None

    decoded_token = decode_auth_token(x_auth_token)

    try:
        id_token = CozyIDToken.model_validate(decoded_token)
    except ValidationError as exc:
        logger.error("Unable to validate the ID token: %s", exc)
        raise unauthorized_http_exception from exc

    cozy_auth_data = validate_auth_against_cozystack(id_token, x_auth_token)

    user = AuthenticatedUser(
        agent={"openid": f"{id_token.iss}/{id_token.sub or "cli"}"},
        scopes=["statements/write", "statements/read/mine"],
        target=cozy_auth_data.model_dump_json(),
    )

    return user

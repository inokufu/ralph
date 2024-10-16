"""OpenID Connect authentication tool for the Ralph API."""

import logging
import os

import httpx
from fastapi import Header, HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Annotated

from ralph.api.auth.token import CozyIDToken
from ralph.api.auth.user import AuthenticatedUser

logger = logging.getLogger(__name__)


class CozyAuthData(BaseModel):
    """Pydantic model representing

    Attributes:
        instance_url (AnyHttpUrl):
        token (str):
        cookie (str):
    """

    instance_url: AnyHttpUrl
    token: str
    cookie: str

    # TODO: validation "Bearer" in auth_token & "cozysessid" in cookie


def get_cozy_user(
    x_auth_token: Annotated[str | None, Header()] = None,
    cookie: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Decode and validate Cozy ID token against Cozy-Stack server.

    Return:
        AuthenticatedUser (AuthenticatedUser)

    Raises:
        HTTPException
    """
    if x_auth_token is None or "Bearer" not in x_auth_token:
        logger.debug(
            "Not using cozy auth. The cozy authentication mode requires a Bearer token"
        )
        return None

    if cookie is None or "cozysessid" not in cookie:
        logger.debug(
            "Not using cozy auth. The cozy authentication mode requires a cozysessid cookie"
        )
        return None

    encoded_token = x_auth_token.split(" ")[-1]

    try:
        decoded_token = jwt.decode(
            encoded_token,
            key=None,
            options={"verify_signature": False, "verify_aud": False},
        )
    except (ExpiredSignatureError, JWTError, JWTClaimsError) as exc:
        logger.error("Unable to decode the ID token: %s", exc)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    id_token = CozyIDToken.model_validate(decoded_token)
    instance_url = os.path.join("http://", id_token.iss)

    # request cozy-stack to check auth is valid
    try:
        response = httpx.get(
            os.path.join(instance_url, "apps/"),
            headers={
                "Accept": "application/json",
                "Authorization": x_auth_token,
                "Cookie": cookie,
            },
        )

        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Unable to authenticate user against cozy-stack: %s", exc)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    cozy_auth_data = CozyAuthData(
        instance_url=instance_url, token=x_auth_token, cookie=cookie
    )

    # TODO: should we replace open_id agent (BaseXapiAgentWithOpenId) by a specific agent for Cozy ?
    # TODO: what about scopes

    user = AuthenticatedUser(
        agent={"openid": f"{id_token.iss}/{id_token.sub}"},
        scopes=["all"],
        target=cozy_auth_data.model_dump_json(),
    )

    logger.info(user)

    return user

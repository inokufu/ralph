"""Cozy related models."""

from pydantic import AnyHttpUrl, BaseModel, field_validator

COZY_AUTH_COOKIE_NAME = "cozysessid"


class CozyAuthData(BaseModel):
    """Pydantic model representing cozy authentication data.

    Attributes:
        instance_url (AnyHttpUrl):
        token (str):
        cookie (str):
    """

    instance_url: AnyHttpUrl
    token: str
    cookie: str

    @field_validator("token")
    @classmethod
    def _check_bearer_token(cls, v: str) -> str:
        if "Bearer" not in v:
            raise ValueError("must contain 'Bearer'")

        return v

    @field_validator("cookie")
    @classmethod
    def _check_auth_cookie(cls, v: str) -> str:
        if COZY_AUTH_COOKIE_NAME not in v:
            raise ValueError(f"must contain '{COZY_AUTH_COOKIE_NAME}'")

        return v

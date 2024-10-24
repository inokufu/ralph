"""Cozy related models."""

from pydantic import AnyHttpUrl, BaseModel, field_validator


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

    @field_validator('token')
    @classmethod
    def _check_bearer_token(cls, v: str) -> str:
        if "Bearer" not in v:
            raise ValueError("must contain 'Bearer'")

        return v

    @field_validator('cookie')
    @classmethod
    def _check_cozysessid_cookie(cls, v: str) -> str:
        if "cozysessid" not in v:
            raise ValueError("must contain 'cozysessid'")

        return v


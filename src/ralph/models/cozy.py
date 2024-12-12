"""Cozy related models."""

from pydantic import AnyHttpUrl, BaseModel, field_validator


class CozyAuthData(BaseModel):
    """Pydantic model representing cozy authentication data.

    Attributes:
        instance_url (AnyHttpUrl): url of cozystack instance.
        token (str): authentication jwt.
    """

    instance_url: AnyHttpUrl
    token: str

    @field_validator("token")
    @classmethod
    def _check_bearer_token(cls, v: str) -> str:
        if "Bearer" not in v:
            raise ValueError("must contain 'Bearer'")

        return v

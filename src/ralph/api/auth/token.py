"""Base IDToken class for the Ralph API."""

from pydantic import BaseModel, ConfigDict


class BaseIDToken(BaseModel):
    """Pydantic model representing the core of an ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements.
    """

    iss: str
    iat: int
    scope: str | None = None
    target: str | None = None

    model_config = ConfigDict(extra="ignore")

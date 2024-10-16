from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BaseIDToken(BaseModel):
    """Pydantic model representing the core of an ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str): Audience(s) that this ID Token is intended for.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements.
    """

    iss: str
    sub: str
    iat: int
    scope: Optional[str] = None
    target: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class OpenIDConnectIDToken(BaseIDToken):
    """Pydantic model representing the core of an OpenID Connect ID Token.

    ID Tokens are polymorphic and may have many attributes not defined in the
    specification. This model ignores all additional fields.

    Attributes:
        iss (str): Issuer Identifier for the Issuer of the response.
        sub (str): Subject Identifier.
        aud (str): Audience(s) that this ID Token is intended for.
        iat (int): Time at which the JWT was issued.
        scope (str): Scope(s) for resource authorization.
        target (str): Target for storing the statements.
        exp (int): Expiration time on or after which the ID Token MUST NOT be
                   accepted for processing.
    """

    aud: Optional[str] = None
    exp: Optional[int] = None


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
        session_id (int): ???
    """

    aud: List[str]
    session_id: str

"""API-specific data models definition.

Allows to be exactly as lax as we want when it comes to exact object shape and
validation.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.xapi.base.agents import BaseXapiAgent
from ..models.xapi.base.groups import BaseXapiGroup


class ErrorDetail(BaseModel):
    """Pydantic model for errors raised detail.

    Type for return value for errors raised in API endpoints.
    Useful for OpenAPI documentation generation.
    """

    detail: str


class BaseModelWithLaxConfig(BaseModel):
    """Pydantic base model with lax configuration.

    Common base lax model to perform light input validation as
    we receive statements through the API.
    """

    model_config = ConfigDict(extra="allow", coerce_numbers_to_str=True)


class LaxObjectField(BaseModelWithLaxConfig):
    """Pydantic model for lax `object` field.

    Lightest definition of an object field compliant to the specification.
    """

    id: str


class LaxVerbField(BaseModelWithLaxConfig):
    """Pydantic model for lax `verb` field.

    Lightest definition of a verb field compliant to the specification.
    """

    id: str


class LaxStatement(BaseModelWithLaxConfig):
    """Pydantic model for lax statement.

    It accepts without validating all fields beyond the bare minimum required to
    qualify an object as an XAPI statement.
    """

    actor: BaseXapiAgent | BaseXapiGroup
    id: UUID | None = None
    object: LaxObjectField
    verb: LaxVerbField

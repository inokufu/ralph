"""Base xAPI `Context` definitions."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import model_validator
from ralph.conf import NonEmptyStrictStr

from ..config import BaseModelWithConfig
from .agents import BaseXapiAgent
from .common import IRI, LanguageTag
from .groups import BaseXapiGroup
from .unnested_objects import BaseXapiActivity, BaseXapiStatementRef


class BaseXapiContextContextActivities(BaseModelWithConfig):
    """Pydantic model for context `contextActivities` property.

    Attributes:
        parent (dict or list): An Activity with a direct relation to the statement's
            Activity.
        grouping (dict or list): An Activity with an indirect relation to the
            statement's Activity.
        category (dict or list): An Activity used to categorize the Statement.
        other (dict or list): A contextActivity that doesn't fit one of the other
            properties.
    """

    parent: Optional[List[BaseXapiActivity]] = None
    grouping: Optional[List[BaseXapiActivity]] = None
    category: Optional[List[BaseXapiActivity]] = None
    other: Optional[List[BaseXapiActivity]] = None

    # TODO: Est-ce le bon endroit pour faire ça ? Ou faudrait-il appliquer cette modif dans le get plutôt ?
    @model_validator(mode="before")
    @classmethod
    def convert_children_to_arrays(cls, values: Any) -> Any:
        """Convert children to arrays if they are not."""
        if not isinstance(values, dict):
            return values

        for k, v in values.items():
            if not isinstance(v, list):
                values[k] = [v]
        return values


class BaseXapiContext(BaseModelWithConfig):
    """Pydantic model for `context` property.

    Attributes:
        registration (UUID): The registration that the Statement is associated with.
        instructor (dict): The instructor that the Statement relates to.
        team (dict): The team that this Statement relates to.
        contextActivities (dict): See BaseXapiContextContextActivities.
        revision (str): The revision of the activity associated with this Statement.
        platform (str): The platform where the learning activity took place.
        language (dict): The language in which the experience occurred.
        statement (dict): Another Statement giving context for this Statement.
        extensions (dict): Consists of a dictionary of other properties as needed.
    """

    registration: Optional[UUID] = None
    instructor: Optional[Union[BaseXapiAgent, BaseXapiGroup]] = None
    team: Optional[BaseXapiGroup] = None
    contextActivities: Optional[BaseXapiContextContextActivities] = None
    revision: Optional[NonEmptyStrictStr] = None
    platform: Optional[NonEmptyStrictStr] = None
    language: Optional[LanguageTag] = None
    statement: Optional[BaseXapiStatementRef] = None
    extensions: Optional[Dict[IRI, Union[str, int, bool, list, dict, None]]] = None

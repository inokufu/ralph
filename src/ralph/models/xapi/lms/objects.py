"""LMS xAPI events object fields definitions."""

from typing import Annotated, Literal

from pydantic import Field

from ..concepts.activity_types.acrossx_profile import (
    WebpageActivity,
    WebpageActivityDefinition,
)
from ..concepts.activity_types.activity_streams_vocabulary import (
    FileActivity,
    FileActivityDefinition,
)
from ..concepts.constants.acrossx_profile import ACTIVITY_EXTENSIONS_TYPE
from ..config import BaseExtensionModelWithConfig

# Page


class LMSPageObjectDefinitionExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for LMS page `object`.`definition`.`extensions` property.

    Attributes:
        type (str): Characterisation of the page. Can be either `course`,
            `course_list`, `user_space` value.
    """

    type: Annotated[
        Literal["course", "course_list", "user_space"] | None,
        Field(alias=ACTIVITY_EXTENSIONS_TYPE),
    ] = None


class LMSPageObjectDefinition(WebpageActivityDefinition):
    """Pydantic model for LMS page `object`.`definition` property.

    Attributes:
        extensions (dict): see LMSPageObjectDefinitionExtensions.
    """

    extensions: LMSPageObjectDefinitionExtensions | None = None


class LMSPageObject(WebpageActivity):
    """Pydantic model for LMS page `object` property.

    Attributes:
        definition (dict): see LMSPageObjectDefinition.
    """

    definition: LMSPageObjectDefinition


# File


class LMSFileObjectDefinitionExtensions(BaseExtensionModelWithConfig):
    """Pydantic model for LMS file `object`.`definition`.`extensions` property.

    Attributes:
        type (str): Characterisation of the MIME type of the file.
    """

    type: Annotated[str, Field(alias=ACTIVITY_EXTENSIONS_TYPE)]


class LMSFileObjectDefinition(FileActivityDefinition):
    """Pydantic model for LMS file `object`.`definition` property.

    Attributes:
        extensions (dict): see LMSFileObjectDefinitionExtensions.
    """

    extensions: LMSFileObjectDefinitionExtensions | None = None


class LMSFileObject(FileActivity):
    """Pydantic model for LMS file `object` property.

    Attributes:
        definition (dict): see LMSFileObjectDefinition.
    """

    definition: LMSFileObjectDefinition

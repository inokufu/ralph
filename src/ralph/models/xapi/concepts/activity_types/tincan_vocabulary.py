"""`Scorm Profile` activity types definitions."""

from typing import Literal

from ...base.unnested_objects import BaseXapiActivity, BaseXapiActivityDefinition

# Document


class DocumentActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for document `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://id.tincanapi.com/activitytype/document`.
    """

    type: Literal["http://id.tincanapi.com/activitytype/document"] = (
        "http://id.tincanapi.com/activitytype/document"
    )


class DocumentActivity(BaseXapiActivity):
    """Pydantic model for document `Activity` type.

    Attributes:
        definition (dict): see DocumentActivityDefinition.
    """

    definition: DocumentActivityDefinition


# Webinar


class WebinarActivityDefinition(BaseXapiActivityDefinition):
    """Pydantic model for webinar `Activity` type `definition` property.

    Attributes:
        type (str): Consists of the value
            `http://id.tincanapi.com/activitytype/webinar`.
    """

    type: Literal["http://id.tincanapi.com/activitytype/webinar"] = (
        "http://id.tincanapi.com/activitytype/webinar"
    )


class WebinarActivity(BaseXapiActivity):
    """Pydantic model for webinar `Activity` type.

    Attributes:
        definition (dict): see WebinarActivityDefinition.
    """

    definition: WebinarActivityDefinition

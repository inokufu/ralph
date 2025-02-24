"""Tests for BaseXapiContext and BaseXapiContextContextActivities."""

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.contexts import (
    BaseXapiActivity,
    BaseXapiContextContextActivities,
)

from tests.factories import mock_xapi_instance


@pytest.mark.parametrize(
    "field",
    ["parent", "grouping", "category", "other"],
)
def test_models_xapi_base_context_activities_ensure_list(field):
    """Test that BaseXapiContextContextActivities fields are always list."""
    activity1 = mock_xapi_instance(BaseXapiActivity)
    activity2 = mock_xapi_instance(BaseXapiActivity)

    context_activity = BaseXapiContextContextActivities.model_validate(
        {field: activity1}
    )

    assert getattr(context_activity, field) == [activity1]

    context_activity = BaseXapiContextContextActivities.model_validate(
        {field: [activity1]}
    )

    assert getattr(context_activity, field) == [activity1]

    context_activity = BaseXapiContextContextActivities.model_validate(
        {field: [activity1, activity2]}
    )

    assert getattr(context_activity, field) == [activity1, activity2]


@pytest.mark.parametrize(
    "field",
    ["parent", "grouping", "category", "other"],
)
def test_models_xapi_base_context_activities_ensure_list_validation_error(field):
    """
    Test that BaseXapiContextContextActivities fields only accepts BaseXapiActivities.
    """
    with pytest.raises(ValidationError):
        BaseXapiContextContextActivities.model_validate({field: "abc"})

    with pytest.raises(ValidationError):
        BaseXapiContextContextActivities.model_validate({field: ["abc", "def"]})

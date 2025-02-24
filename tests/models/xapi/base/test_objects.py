"""Tests for the base xAPI `Object` definitions."""

import pytest
from pydantic import ValidationError

from ralph.models.xapi.base.agents import (
    BaseXapiAgentWithAccount,
    BaseXapiAgentWithMbox,
    BaseXapiAgentWithMboxSha1Sum,
    BaseXapiAgentWithOpenId,
)
from ralph.models.xapi.base.groups import (
    BaseXapiAnonymousGroup,
    BaseXapiIdentifiedGroupWithAccount,
    BaseXapiIdentifiedGroupWithMbox,
    BaseXapiIdentifiedGroupWithMboxSha1Sum,
    BaseXapiIdentifiedGroupWithOpenId,
)
from ralph.models.xapi.base.objects import BaseXapiSubStatement
from ralph.models.xapi.base.unnested_objects import (
    BaseXapiActivity,
    BaseXapiStatementRef,
)
from ralph.models.xapi.base.verbs import BaseXapiVerb

from tests.factories import mock_xapi_instance


def test_models_xapi_object_base_sub_statement_type_with_valid_field():
    """Test a valid BaseXapiSubStatement has the expected `objectType` value."""
    field = mock_xapi_instance(BaseXapiSubStatement)

    assert field.objectType == "SubStatement"


@pytest.mark.parametrize(
    "object_class",
    [
        BaseXapiAgentWithMbox,
        BaseXapiAgentWithAccount,
        BaseXapiAgentWithMboxSha1Sum,
        BaseXapiAgentWithOpenId,
        BaseXapiAnonymousGroup,
        BaseXapiIdentifiedGroupWithMbox,
        BaseXapiIdentifiedGroupWithMboxSha1Sum,
        BaseXapiIdentifiedGroupWithOpenId,
        BaseXapiIdentifiedGroupWithAccount,
        BaseXapiActivity,
        BaseXapiStatementRef,
    ],
)
def test_models_xapi_object_base_sub_statement_object(object_class):
    """Test BaseXapiSubStatement Object with multiple values."""
    sub_statement_as_dict = mock_xapi_instance(BaseXapiSubStatement).model_dump()

    sub_statement_as_dict["object"] = mock_xapi_instance(object_class).model_dump()

    sub_statement = BaseXapiSubStatement.model_validate(sub_statement_as_dict)

    assert isinstance(sub_statement.object, object_class)

def test_models_xapi_object_base_sub_statement_object_validation_error():
    """Test BaseXapiSubStatement Object validation error."""
    sub_statement_as_dict = mock_xapi_instance(BaseXapiSubStatement).model_dump()

    sub_statement_as_dict["object"] = mock_xapi_instance(BaseXapiVerb)

    with pytest.raises(ValidationError):
        BaseXapiSubStatement.model_validate(sub_statement_as_dict)


"""Tests for the xAPI navigation statements."""

from ralph.models.xapi.navigation.statements import PageTerminated, PageViewed

from tests.factories import mock_xapi_instance


def test_models_xapi_navigation_page_terminated_with_valid_statement():
    """Test that a valid page_terminated statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """
    statement = mock_xapi_instance(PageTerminated)
    assert statement.verb.id == "http://adlnet.gov/expapi/verbs/terminated"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"


def test_models_xapi_page_viewed_with_valid_statement():
    """Test that a valid page_viewed statement has the expected `verb`.`id` and
    `object`.`definition`.`type` property values.
    """
    statement = mock_xapi_instance(PageViewed)
    assert statement.verb.id == "http://id.tincanapi.com/verb/viewed"
    assert statement.object.definition.type == "http://activitystrea.ms/schema/1.0/page"

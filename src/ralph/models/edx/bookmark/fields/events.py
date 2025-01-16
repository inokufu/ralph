"""Video event fields definitions."""

from typing import Annotated, Literal

from pydantic import StringConstraints

from ...base import AbstractBaseEventField


class EdxBookmarkBaseEventField(AbstractBaseEventField):
    """Pydantic model for bookmark core `event` field.

    Attributes:
        bookmark_id (str): Consists of the unique internal identifier for the
            bookmark.
        component_type (str): Consists of the component type of the bookmarked
            XBlock.
        component_usage_id (str): Consists of the unique usage identifier of the
            bookmarked XBlock.
    """

    bookmark_id: str
    component_type: Literal[
        "chapter",
        "course",
        "discussion",
        "html",
        "problem",
        "sequential",
        "vertical",
        "video",
    ]
    component_usage_id: Annotated[
        str,
        StringConstraints(
            pattern=(
                r"^block-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+"
                r"type@([a-z]+)\+block@[a-f0-9]{32}$"
            )
        ),
    ]


class EdxBookmarkAddedEventField(EdxBookmarkBaseEventField):
    """Pydantic model for `edx.bookmark.added` `event` field.

    Attributes:
        course_id (str): Consists of the identifier of the course that includes
            the bookmark.
    """

    course_id: Annotated[str, StringConstraints(pattern=r"^$|^course-v1:.+\+.+\+.+$")]


class EdxBookmarkListedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.bookmark.listed` `event` field.

    Attributes:
        bookmarks_count (str): Consists of the number of pages a learner has bookmarked.
        course_id (str): Consists of the identifier of the course that includes
            the bookmark.
        list_type (str): Consists of either `per_course` or `all_courses` value.
        page_number(int): Consists of the current page number in the list of
            bookmarks.
        page_size (int): Consists of the number of bookmarks on the current page.
    """

    bookmarks_count: int
    course_id: (
        Annotated[str, StringConstraints(pattern=r"^$|^course-v1:.+\+.+\+.+$")] | None
    )
    list_type: Literal["per_course", "all_courses"]
    page_number: int
    page_size: int


class EdxBookmarkRemovedEventField(EdxBookmarkBaseEventField):
    """Pydantic model for `edx.bookmark.removed` `event` field.

    Attributes:
        course_id (str): Consists of the identifier of the course that includes
            the bookmark.
    """

    course_id: Annotated[str, StringConstraints(pattern=r"^$|^course-v1:.+\+.+\+.+$")]


class UIEdxCourseToolAccessedEventField(AbstractBaseEventField):
    """Pydantic model for `edx.course.tool.accessed` `event` field.

    Attributes:
        tool_name (str): Consists of either `edx.bookmarks`, `edx.reviews`
            and `edx.updates`.
    """

    tool_name: Literal["edx.bookmarks", "edx.reviews", "edx.updates"]

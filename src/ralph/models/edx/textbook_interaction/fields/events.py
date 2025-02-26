"""Textbook interaction event fields definitions."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from ...base import AbstractBaseEventField


class TextbookInteractionBaseEventField(AbstractBaseEventField):
    """Pydantic model for textbook interaction core `event` field.

    Attributes:
        chapter (str): Consists of the name of the PDF file.
            It begins with the `block_id` value and ends with the `.pdf` extension.
        page (int): The number of the page that is open when the event is emitted.
    """

    page: int
    chapter: Annotated[
        str,
        StringConstraints(
            pattern=r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"
        ),
    ]


class TextbookPdfThumbnailsToggledEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.thumbnails.toggled`.`event` field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.thumbnails.toggled`.
    """

    name: Literal["textbook.pdf.thumbnails.toggled"]


class TextbookPdfThumbnailNavigatedEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.thumbnail.navigated`.`event` field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.thumbnail.navigated`.
        thumbnail_title (str): Consists of the name of the thumbnail.
    """

    name: Literal["textbook.pdf.thumbnail.navigated"]
    thumbnail_title: str


class TextbookPdfOutlineToggledEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.outline.toggled`.`event` field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.outline.toggled`.
    """

    name: Literal["textbook.pdf.outline.toggled"]


class TextbookPdfChapterNavigatedEventField(AbstractBaseEventField):
    """Pydantic model for `textbook.pdf.chapter.navigated`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.chapter.navigated`.
        chapter (str): Consists of the name of the PDF file.
            It begins with the `block_id` value and ends with the `.pdf` extension.
    """

    name: Literal["textbook.pdf.chapter.navigated"]
    chapter: Annotated[
        str,
        StringConstraints(
            pattern=r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"
        ),
    ]
    chapter_title: str


class TextbookPdfPageNavigatedEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.page.navigated`.`event` field.

    Attribute:
        name (str): Consists of the value `textbook.pdf.page.navigated`.
    """

    name: Literal["textbook.pdf.page.navigated"]


class TextbookPdfZoomButtonsChangedEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.zoom.buttons.changed`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.zoom.buttons.changed`.
        direction (str): Consists of either the `in` or `out` value.
    """

    name: Literal["textbook.pdf.zoom.buttons.changed"]
    direction: Literal["in", "out"]


class TextbookPdfZoomMenuChangedEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.zoom.menu.changed`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.zoom.menu.changed`.
        amount (str): Consists either of the `0.5`, `0.75`, `1`, `1.25`, `1.5`, `2`,
            `3`, `4`, `auto`, `custom`, `page-actual`, `page-fit`, `page-width` value.
    """

    name: Literal["textbook.pdf.zoom.menu.changed"]
    amount: Literal[
        "0.5",
        "0.75",
        "1",
        "1.25",
        "1.5",
        "2",
        "3",
        "4",
        "auto",
        "custom",
        "page-actual",
        "page-fit",
        "page-width",
    ]


class TextbookPdfDisplayScaledEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.display.scaled`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.display.scaled`.
        amount (str): Consists of a floating point number string value.
    """

    name: Literal["textbook.pdf.display.scaled"]
    amount: float


class TextbookPdfPageScrolledEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.page.scrolled`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.page.scrolled`.
        direction (str): Consists either of the `up` or `down` value.
    """

    name: Literal["textbook.pdf.page.scrolled"]
    direction: Literal["up", "down"]


class TextbookPdfSearchExecutedEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.search.executed`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.executed`.
        caseSensitive (bool): Consists either of the `true` value if the case-sensitive
            option is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to
            highlight all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that
            is unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.executed"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchNavigatedNextEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.search.navigatednext`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.navigatednext`.
        caseSensitive (bool): Consists either of the `true` value if the case-sensitive
            option is selected or `false` if this option is not selected.
        findPrevious(bool): Consists either of the ‘true’ value if the user clicks the
            Find Previous icon or ‘false’ if the user clicks the <kbd>Find Next</kbd>
            icon.
        highlightAll (bool): Consists either of the `true` value if the option to
            highlight all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that
            is unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.navigatednext"]
    caseSensitive: bool
    findPrevious: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchHighlightToggledEventField(TextbookInteractionBaseEventField):
    """Pydantic model for `textbook.pdf.search.highlight.toggled`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.search.highlight.toggled`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive
            option is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to
            highlight all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that
            is unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.search.highlight.toggled"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class TextbookPdfSearchCaseSensitivityToggledEventField(
    TextbookInteractionBaseEventField
):
    """Pydantic model for `textbook.pdf.searchcasesensitivity.toggled`.`event` field.

    Attributes:
        name (str): Consists of the value `textbook.pdf.searchcasesensitivity.toggled`.
        caseSensitive (bool): Consists either of the `true` value if the case sensitive
            option is selected or `false` if this option is not selected.
        highlightAll (bool): Consists either of the `true` value if the option to
            highlight all matches is selected or `false` if this option is not selected.
        query (str): Consists of the value in the search field.
        status (str): Consists either of the value `not found` for a search string that
            is unsuccessful or blank for successful search strings.
    """

    name: Literal["textbook.pdf.searchcasesensitivity.toggled"]
    caseSensitive: bool
    highlightAll: bool
    query: str
    status: str


class BookEventField(AbstractBaseEventField):
    """Pydantic model for `book`.`event` field.

    Attributes:
        chapter (str): Consists of the name of the PDF file.
        name (str): Consists of `textbook.pdf.page.loaded` if type is set to
            `gotopage`,
            `textbook.pdf.page.navigatednext` if type is set to `prevpage`,
            `textbook.pdf.page.navigatednext` if type is set to `nextpage`.
        new (int): Consists of the destination page number.
        old (int): Consists of the original page number. It applies to `gotopage` event
            types only.
        type (str): Consists of `gotopage` value when a page loads after the student
            manually enters its number, `prevpage` value when the next page button is
            clicked or `nextpage` value when the previous page button is clicked.
    """

    chapter: Annotated[
        str,
        StringConstraints(
            pattern=r"^\/asset-v1:[^\/+]+(\/|\+)[^\/+]+(\/|\+)[^\/?]+type@asset\+block.+$"
        ),
    ]
    name: Literal["textbook.pdf.page.loaded", "textbook.pdf.page.navigatednext"]
    new: int
    old: int | None = None
    type: Annotated[
        Literal["gotopage", "prevpage", "nextpage"],
        Field(alias="type"),
    ]

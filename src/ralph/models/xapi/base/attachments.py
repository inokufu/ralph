"""Base xAPI `Attachments` definitions."""

from pydantic import AnyUrl, Field

from ..config import BaseModelWithConfig
from .common import IRI, LanguageMap


class BaseXapiAttachment(BaseModelWithConfig):
    """Pydantic model for `attachment` property.

    Attributes:
        usageType (IRI): Identifies the usage of this Attachment.
        display (LanguageMap): Consists of the Attachment's title.
        description (LanguageMap): Consists of the Attachment's description.
        contentType (str): Consists of the Attachment's content type.
        length (int): Consists of the length of the Attachment's data in octets.
        sha2 (str): Consists of the SHA-2 hash of the Attachment data.
        fileUrl (URL): Consists of the URL from which the Attachment can be retrieved.
    """

    usageType: IRI = Field(examples=["http://adlnet.gov/expapi/attachments/signature"])
    display: LanguageMap = Field(examples=[{"en-US": "Signature"}])
    description: LanguageMap | None = Field(
        None, examples=[{"en-US": "A test signature"}]
    )
    contentType: str = Field(examples=["application/octet-stream"])
    length: int = Field(examples=[4235])
    sha2: str = Field(
        examples=["672fa5fa658017f1b72d65036f13379c6ab05d4ab3b6664908d8acf0b6a0c634"]
    )
    fileUrl: AnyUrl | None = Field(None, examples=["http://example.com/myfile"])

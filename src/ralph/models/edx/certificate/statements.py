"""Certificate events model definitions."""

from typing import Literal

from pydantic import Json

from ralph.models.selector import selector

from ..server import BaseServerModel
from .fields.events import (
    CertificateGenerationBaseEventField,
    EdxCertificateCreatedEventField,
    EdxCertificateEvidenceVisitedEventField,
    EdxCertificateRevokedEventField,
    EdxCertificateSharedEventField,
)


class EdxCertificateCreated(BaseServerModel):
    """Pydantic model for `edx.certificate.created` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.created`.
        name (str): Consists of the value `edx.certificate.created`.
    """

    __selector__ = selector(event_source="server", event_type="edx.certificate.created")

    event: Json[EdxCertificateCreatedEventField] | EdxCertificateCreatedEventField
    event_type: Literal["edx.certificate.created"]
    name: Literal["edx.certificate.created"]


class EdxCertificateRevoked(BaseServerModel):
    """Pydantic model for `edx.certificate.revoked` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.revoked`.
        name (str): Consists of the value `edx.certificate.revoked`.
    """

    __selector__ = selector(event_source="server", event_type="edx.certificate.revoked")

    event: Json[EdxCertificateRevokedEventField] | EdxCertificateRevokedEventField
    event_type: Literal["edx.certificate.revoked"]
    name: Literal["edx.certificate.revoked"]


class EdxCertificateShared(BaseServerModel):
    """Pydantic model for `edx.certificate.shared` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.shared`.
        name (str): Consists of the value `edx.certificate.shared`.
    """

    __selector__ = selector(event_source="server", event_type="edx.certificate.shared")

    event: Json[EdxCertificateSharedEventField] | EdxCertificateSharedEventField

    event_type: Literal["edx.certificate.shared"]
    name: Literal["edx.certificate.shared"]


class EdxCertificateEvidenceVisited(BaseServerModel):
    """Pydantic model for `edx.certificate.evidence_visited` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.evidence_visited`.
        name (str): Consists of the value `edx.certificate.evidence_visited`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.certificate.evidence_visited"
    )

    event: (
        Json[EdxCertificateEvidenceVisitedEventField]
        | EdxCertificateEvidenceVisitedEventField
    )
    event_type: Literal["edx.certificate.evidence_visited"]
    name: Literal["edx.certificate.evidence_visited"]


class EdxCertificateGenerationEnabled(BaseServerModel):
    """Pydantic model for `edx.certificate.generation.enabled` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.generation.enabled`.
        name (str): Consists of the value `edx.certificate.generation.enabled`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.certificate.generation.enabled"
    )

    event: (
        Json[CertificateGenerationBaseEventField] | CertificateGenerationBaseEventField
    )
    event_type: Literal["edx.certificate.generation.enabled"]
    name: Literal["edx.certificate.generation.enabled"]


class EdxCertificateGenerationDisabled(BaseServerModel):
    """Pydantic model for `edx.certificate.generation.disabled` statement.

    Attributes:
        event_type (str): Consists of the value `edx.certificate.generation.disabled`.
        name (str): Consists of the value `edx.certificate.generation.disabled`.
    """

    __selector__ = selector(
        event_source="server", event_type="edx.certificate.generation.disabled"
    )

    event: CertificateGenerationBaseEventField | CertificateGenerationBaseEventField
    event_type: Literal["edx.certificate.generation.disabled"]
    name: Literal["edx.certificate.generation.disabled"]

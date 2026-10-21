from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)


@dataclass(frozen=True, slots=True)
class ListDocumentTypesQuery:
    organization_id: OrganizationId
    include_inactive: bool = False


@dataclass(frozen=True, slots=True)
class GetComplianceDocumentQuery:
    organization_id: OrganizationId
    document_id: ComplianceDocumentId


@dataclass(frozen=True, slots=True)
class ListComplianceDocumentsQuery:
    organization_id: OrganizationId
    document_type_ids: tuple[DocumentTypeId, ...] = field(default_factory=tuple)
    status: ComplianceDocumentStatus | None = None
    subject_kind: DocumentSubjectKind | None = None
    review_due: bool | None = None
    search: str | None = None
    include_archived: bool = False
    offset: int = 0
    limit: int = 50

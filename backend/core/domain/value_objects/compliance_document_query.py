from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
)
from backend.core.domain.value_objects.safety_ids import DocumentTypeId


@dataclass(frozen=True, slots=True)
class ComplianceDocumentReviewDueFilter:
    """Keep only review-due documents (D11), evaluated per document type.

    ``document_types`` must hold the type of every document the other criteria
    keep, inactive types included (``list(organization_id, include_inactive=True)``);
    a missing type raises ``ValueError``.
    """

    as_of: date
    document_types: Mapping[DocumentTypeId, DocumentType]


@dataclass(frozen=True, slots=True)
class ComplianceDocumentQuery:
    """Registry query; ``document_type_ids=None`` means any type."""

    organization_id: OrganizationId
    document_type_ids: frozenset[DocumentTypeId] | None = None
    status: ComplianceDocumentStatus | None = None
    subject_kind: DocumentSubjectKind | None = None
    review_due: ComplianceDocumentReviewDueFilter | None = None
    include_archived: bool = False
    search: str | None = None
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class ComplianceDocumentPage:
    items: tuple[ComplianceDocument, ...]
    total: int
    offset: int
    limit: int

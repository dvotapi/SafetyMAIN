from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final
from uuid import UUID

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_document_components import (
    DocumentApplicability,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentSource
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    DocumentTypeId,
)

UNSET: Final[object] = object()
"""Sentinel distinguishing "field omitted" from an explicit ``None``.

The domain ``update_details`` uses ``...`` for the same purpose; handlers map
``UNSET`` to ``...`` before calling it.
"""


@dataclass(frozen=True, slots=True)
class CreateComplianceDocumentCommand:
    organization_id: OrganizationId
    actor_id: UserId
    document_type_id: DocumentTypeId
    code: str
    title: str
    subject_id: UUID | None = None
    issued_at: date | None = None
    effective_from: date | None = None
    next_review_at: date | None = None
    approved_by_document_id: ComplianceDocumentId | None = None
    supersedes_document_id: ComplianceDocumentId | None = None
    applicability: DocumentApplicability | None = None
    source: ComplianceDocumentSource = ComplianceDocumentSource.MANUAL
    notes: str = ""
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateComplianceDocumentCommand:
    """Partial update of a draft compliance document.

    Nullable fields default to ``UNSET`` ("field omitted"); ``None`` clears the
    corresponding attribute, matching the domain ``update_details`` contract.
    """

    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    code: str | None = None
    title: str | None = None
    issued_at: date | None | object = UNSET
    effective_from: date | None | object = UNSET
    next_review_at: date | None | object = UNSET
    approved_by_document_id: ComplianceDocumentId | None | object = UNSET
    supersedes_document_id: ComplianceDocumentId | None | object = UNSET
    applicability: DocumentApplicability | None = None
    notes: str | None = None
    audit_context: AuditContext | None = None

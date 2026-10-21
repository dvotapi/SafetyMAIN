from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId


@dataclass(frozen=True, slots=True)
class ApproveComplianceDocumentCommand:
    """Draft -> approved."""

    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ActivateComplianceDocumentCommand:
    """Approved -> active.

    Superseding the previous edition happens atomically in the same unit of
    work when ``supersedes_document_id`` is set on this document.
    """

    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class StartReviewComplianceDocumentCommand:
    """Active -> under_review."""

    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class CompleteReviewComplianceDocumentCommand:
    """Under_review -> active with ``next_review_at`` recomputed from ``completed_on`` (D7)."""

    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    completed_on: date
    next_review_at: date | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ArchiveComplianceDocumentCommand:
    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RestoreComplianceDocumentCommand:
    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None

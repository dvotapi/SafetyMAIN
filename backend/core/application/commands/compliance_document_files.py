from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.safety_ids import ComplianceDocumentId


@dataclass(frozen=True, slots=True)
class CreateComplianceDocumentUploadUrlCommand:
    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ConfirmComplianceDocumentFileCommand:
    organization_id: OrganizationId
    document_id: ComplianceDocumentId
    actor_id: UserId
    expected_version: int
    key: str
    size_bytes: int
    sha256: str
    content_type: str
    original_filename: str
    audit_context: AuditContext | None = None

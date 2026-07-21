from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import audit_event_in_scope
from backend.core.application.audit.failure_codes import AUDITABLE_ADMIN_FAILURES
from backend.core.application.audit.metadata import (
    changed_fields_metadata,
    role_change_metadata,
    status_change_metadata,
)
from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)

__all__ = [
    "AUDITABLE_ADMIN_FAILURES",
    "AdministrativeAuditRecorder",
    "AuditContext",
    "AuditRecordSpec",
    "audit_event_in_scope",
    "changed_fields_metadata",
    "role_change_metadata",
    "status_change_metadata",
]

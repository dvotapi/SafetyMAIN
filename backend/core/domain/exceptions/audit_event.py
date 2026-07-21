from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects.audit_event_id import AuditEventId


class AuditEventError(SafetyMainDomainError):
    """Base class for audit event domain errors."""


class AuditEventNotFound(AuditEventError):
    def __init__(self, audit_event_id: AuditEventId) -> None:
        self.audit_event_id = audit_event_id
        super().__init__(f"Audit event was not found: {audit_event_id.value}")

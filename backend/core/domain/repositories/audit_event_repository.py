from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
)


class AuditEventRepositoryContract(Protocol):
    def add(self, event: AuditEvent) -> None:
        ...

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        ...

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        ...

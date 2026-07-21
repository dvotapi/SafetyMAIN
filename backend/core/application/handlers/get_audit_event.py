from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import audit_event_in_scope
from backend.core.application.queries.audit_events import GetAuditEventQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound


class GetAuditEventHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: GetAuditEventQuery) -> AuditEvent:
        event = self._unit_of_work.audit_events.get(query.audit_event_id)
        if not audit_event_in_scope(event, query.scope_organization_id):
            raise AuditEventNotFound(query.audit_event_id)
        return event

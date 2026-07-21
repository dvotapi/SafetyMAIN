from __future__ import annotations

from backend.core.application.queries.audit_events import ListAuditEventsQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
)


class ListAuditEventsHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work

    def handle(self, query: ListAuditEventsQuery) -> AuditEventListResult:
        if query.target_organization_id is not None and (
            query.target_organization_id != query.scope_organization_id
        ):
            return AuditEventListResult(items=(), total=0, offset=query.offset, limit=query.limit)

        criteria = AuditEventListCriteria(
            scope_organization_id=query.scope_organization_id,
            offset=query.offset,
            limit=query.limit,
            action=query.action,
            resource_type=query.resource_type,
            resource_id=query.resource_id,
            actor_user_id=query.actor_user_id,
            outcome=query.outcome,
            target_organization_id=query.target_organization_id,
            occurred_from=query.occurred_from,
            occurred_to=query.occurred_to,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.audit_events.list_events(criteria)

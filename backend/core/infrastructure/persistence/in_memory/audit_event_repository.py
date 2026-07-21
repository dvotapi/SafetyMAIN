from __future__ import annotations

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound
from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
)


def _is_in_scope(event: AuditEvent, criteria: AuditEventListCriteria) -> bool:
    scope_id = criteria.scope_organization_id
    return (
        event.authorization_organization_id == scope_id
        or event.target_organization_id == scope_id
    )


class InMemoryAuditEventRepository(AuditEventRepositoryContract):
    def __init__(self) -> None:
        self._events_by_id: dict[AuditEventId, AuditEvent] = {}

    def add(self, event: AuditEvent) -> None:
        self._events_by_id[event.id] = event

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        event = self._events_by_id.get(audit_event_id)
        if event is None:
            raise AuditEventNotFound(audit_event_id)
        return event

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        events = [
            event
            for event in self._events_by_id.values()
            if _is_in_scope(event, criteria)
        ]

        if criteria.action is not None:
            events = [event for event in events if event.action is criteria.action]
        if criteria.resource_type is not None:
            events = [
                event
                for event in events
                if event.resource_type is criteria.resource_type
            ]
        if criteria.resource_id is not None:
            events = [
                event for event in events if event.resource_id == criteria.resource_id
            ]
        if criteria.actor_user_id is not None:
            events = [
                event for event in events if event.actor_user_id == criteria.actor_user_id
            ]
        if criteria.outcome is not None:
            events = [event for event in events if event.outcome is criteria.outcome]
        if criteria.target_organization_id is not None:
            events = [
                event
                for event in events
                if event.target_organization_id == criteria.target_organization_id
            ]
        if criteria.occurred_from is not None:
            events = [
                event for event in events if event.occurred_at >= criteria.occurred_from
            ]
        if criteria.occurred_to is not None:
            events = [
                event for event in events if event.occurred_at <= criteria.occurred_to
            ]

        events.sort(key=lambda event: event.id.value)
        events.sort(key=lambda event: event.occurred_at, reverse=not criteria.sort_ascending)
        total = len(events)
        page = events[criteria.offset : criteria.offset + criteria.limit]

        return AuditEventListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def snapshot(self) -> dict[AuditEventId, AuditEvent]:
        return dict(self._events_by_id)

    def restore(self, snapshot: dict[AuditEventId, AuditEvent]) -> None:
        self._events_by_id = dict(snapshot)

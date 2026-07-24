from __future__ import annotations

from backend.core.application.queries.audit_events import ListAuditEventsQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.security_events.query_resolution import (
    audit_actions_for_category,
    audit_actions_for_significance,
    intersect_action_filters,
)
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
            return AuditEventListResult(
                items=(),
                total=0,
                offset=query.offset,
                limit=query.limit,
            )

        event_name_actions = (
            frozenset({query.event_name}) if query.event_name is not None else None
        )
        category_actions = (
            audit_actions_for_category(query.event_category)
            if query.event_category is not None
            else None
        )
        severity_actions = (
            audit_actions_for_significance(query.severity)
            if query.severity is not None
            else None
        )
        explicit_action = frozenset({query.action}) if query.action is not None else None
        actions = intersect_action_filters(
            event_name_actions,
            category_actions,
            severity_actions,
            explicit_action,
        )

        criteria = AuditEventListCriteria(
            scope_organization_id=query.scope_organization_id,
            offset=query.offset,
            limit=query.limit,
            actions=actions,
            resource_type=query.resource_type,
            resource_id=query.resource_id,
            actor_user_id=query.actor_user_id,
            outcome=query.outcome,
            target_organization_id=query.target_organization_id,
            request_id=query.request_id,
            occurred_from=query.occurred_from,
            occurred_to=query.occurred_to,
            sort_ascending=query.sort_ascending,
        )
        return self._unit_of_work.audit_events.list_events(criteria)

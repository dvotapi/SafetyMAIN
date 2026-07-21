from __future__ import annotations

from backend.api.schemas.admin_audit_events import AuditEventListResponse, AuditEventResponse
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects.audit_event_list_criteria import AuditEventListResult


def to_audit_event_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id.value,
        actor_user_id=event.actor_user_id.value if event.actor_user_id else None,
        authorization_organization_id=(
            event.authorization_organization_id.value
            if event.authorization_organization_id
            else None
        ),
        target_organization_id=(
            event.target_organization_id.value if event.target_organization_id else None
        ),
        action=event.action.value,
        resource_type=event.resource_type.value,
        resource_id=event.resource_id,
        outcome=event.outcome.value,
        failure_code=event.failure_code,
        metadata=event.metadata,
        occurred_at=event.occurred_at,
    )


def to_audit_event_list_response(result: AuditEventListResult) -> AuditEventListResponse:
    return AuditEventListResponse(
        items=[to_audit_event_response(event) for event in result.items],
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )

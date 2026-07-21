from __future__ import annotations

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditEventModel,
)


def to_model(event: AuditEvent) -> AuditEventModel:
    return AuditEventModel(
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
        metadata_json=event.metadata,
        occurred_at=event.occurred_at,
    )


def to_domain(model: AuditEventModel) -> AuditEvent:
    return AuditEvent(
        id=AuditEventId(value=model.id),
        actor_user_id=UserId(value=model.actor_user_id) if model.actor_user_id else None,
        authorization_organization_id=(
            OrganizationId(value=model.authorization_organization_id)
            if model.authorization_organization_id
            else None
        ),
        target_organization_id=(
            OrganizationId(value=model.target_organization_id)
            if model.target_organization_id
            else None
        ),
        action=AuditAction(model.action),
        resource_type=AuditResourceType(model.resource_type),
        resource_id=model.resource_id,
        outcome=AuditOutcome(model.outcome),
        failure_code=model.failure_code,
        metadata=dict(model.metadata_json),
        occurred_at=model.occurred_at,
    )

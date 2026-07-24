from __future__ import annotations

from backend.api.schemas.admin_audit_events import (
    AuditChainIntegrityResponse,
    AuditEventListResponse,
    AuditEventResponse,
)
from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.security_events.registry import security_event_descriptor_for
from backend.core.domain.services.audit_integrity_service import (
    AuditChainVerificationResult,
)
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListResult,
)


def to_audit_event_response(event: AuditEvent) -> AuditEventResponse:
    descriptor = security_event_descriptor_for(event.action.value)
    request_id = event.metadata.get("request_id")
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
        event_name=event.action.value,
        event_category=(
            descriptor.category.value if descriptor is not None else "ADMINISTRATIVE"
        ),
        severity=(
            descriptor.default_security_significance.value
            if descriptor is not None and descriptor.default_security_significance is not None
            else None
        ),
        action=event.action.value,
        resource_type=event.resource_type.value,
        resource_id=event.resource_id,
        outcome=event.outcome.value,
        failure_code=event.failure_code,
        request_id=request_id if isinstance(request_id, str) else None,
        metadata=event.metadata,
        occurred_at=event.occurred_at,
        previous_integrity_hash=(
            event.previous_integrity_hash.value if event.previous_integrity_hash else None
        ),
        integrity_hash=event.integrity_hash.value if event.integrity_hash else None,
        integrity_version=(
            event.integrity_version.value if event.integrity_version is not None else None
        ),
    )


def to_audit_chain_integrity_response(
    result: AuditChainVerificationResult,
) -> AuditChainIntegrityResponse:
    return AuditChainIntegrityResponse(
        organization_id=result.organization_id.value,
        valid=result.valid,
        checked_event_count=result.checked_event_count,
        first_invalid_event_id=(
            result.first_invalid_event_id.value if result.first_invalid_event_id else None
        ),
        reason=result.reason.value if result.reason else None,
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

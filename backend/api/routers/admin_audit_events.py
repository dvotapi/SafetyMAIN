from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import (
    get_audit_event_id,
    get_get_audit_event_handler,
    get_list_audit_events_handler,
    require_permission,
)
from backend.api.mappers.admin_audit_events import (
    to_audit_event_list_response,
    to_audit_event_response,
)
from backend.api.openapi import PROTECTED_BUSINESS_ERROR_RESPONSES, success_response
from backend.api.operation_ids import GET_AUDIT_EVENT, LIST_AUDIT_EVENTS
from backend.api.schemas.admin_audit_events import AuditEventListResponse, AuditEventResponse
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import AUDIT_READ
from backend.core.application.handlers.get_audit_event import GetAuditEventHandler
from backend.core.application.handlers.list_audit_events import ListAuditEventsHandler
from backend.core.application.queries.audit_events import GetAuditEventQuery, ListAuditEventsQuery
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

router = APIRouter(prefix="/admin/audit-events", tags=["Admin Audit Events"])


@router.get(
    "",
    response_model=AuditEventListResponse,
    operation_id=LIST_AUDIT_EVENTS,
    summary="List audit events",
    responses={
        **success_response(model=AuditEventListResponse, description="Audit events returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_audit_events(
    tenant_context: Annotated[TenantContext, Depends(require_permission(AUDIT_READ))],
    handler: Annotated[ListAuditEventsHandler, Depends(get_list_audit_events_handler)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    action: Annotated[AuditAction | None, Query()] = None,
    resource_type: Annotated[AuditResourceType | None, Query()] = None,
    resource_id: Annotated[UUID | None, Query()] = None,
    actor_user_id: Annotated[UUID | None, Query()] = None,
    outcome: Annotated[AuditOutcome | None, Query()] = None,
    target_organization_id: Annotated[UUID | None, Query()] = None,
    occurred_from: Annotated[datetime | None, Query()] = None,
    occurred_to: Annotated[datetime | None, Query()] = None,
    sort_ascending: Annotated[bool, Query()] = False,
) -> AuditEventListResponse:
    result = handler.handle(
        ListAuditEventsQuery(
            scope_organization_id=tenant_context.organization_id,
            offset=offset,
            limit=limit,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_user_id=UserId(value=actor_user_id) if actor_user_id else None,
            outcome=outcome,
            target_organization_id=(
                OrganizationId(value=target_organization_id)
                if target_organization_id
                else None
            ),
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            sort_ascending=sort_ascending,
        )
    )
    return to_audit_event_list_response(result)


@router.get(
    "/{audit_event_id}",
    response_model=AuditEventResponse,
    operation_id=GET_AUDIT_EVENT,
    summary="Get an audit event",
    responses={
        **success_response(model=AuditEventResponse, description="Audit event returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_audit_event(
    tenant_context: Annotated[TenantContext, Depends(require_permission(AUDIT_READ))],
    audit_event_id: Annotated[AuditEventId, Depends(get_audit_event_id)],
    handler: Annotated[GetAuditEventHandler, Depends(get_get_audit_event_handler)],
) -> AuditEventResponse:
    event = handler.handle(
        GetAuditEventQuery(
            audit_event_id=audit_event_id,
            scope_organization_id=tenant_context.organization_id,
        )
    )
    return to_audit_event_response(event)

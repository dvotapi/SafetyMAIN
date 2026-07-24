from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    get_audit_event_id,
    get_get_audit_event_handler,
    get_list_audit_events_handler,
    get_verify_audit_chain_handler,
    require_permission,
)
from backend.api.mappers.admin_audit_events import (
    to_audit_chain_integrity_response,
    to_audit_event_list_response,
    to_audit_event_response,
)
from backend.api.openapi import PROTECTED_BUSINESS_ERROR_RESPONSES, success_response
from backend.api.operation_ids import (
    GET_AUDIT_EVENT,
    LIST_AUDIT_EVENTS,
    VERIFY_AUDIT_CHAIN_INTEGRITY,
)
from backend.api.params.audit_event_investigation import (
    AuditEventInvestigationParams,
    get_audit_event_investigation_params,
)
from backend.api.schemas.admin_audit_events import (
    AuditChainIntegrityResponse,
    AuditEventListResponse,
    AuditEventResponse,
)
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import (
    AUDIT_READ,
)
from backend.core.application.handlers.get_audit_event import GetAuditEventHandler
from backend.core.application.handlers.list_audit_events import ListAuditEventsHandler
from backend.core.application.handlers.verify_audit_chain import VerifyAuditChainHandler
from backend.core.application.queries.audit_events import (
    GetAuditEventQuery,
    ListAuditEventsQuery,
)
from backend.core.application.queries.verify_audit_chain import VerifyAuditChainQuery
from backend.core.domain.value_objects.audit_event_id import AuditEventId

router = APIRouter(prefix="/admin/audit-events", tags=["Admin Audit Events"])


@router.get(
    "",
    response_model=AuditEventListResponse,
    operation_id=LIST_AUDIT_EVENTS,
    summary="List audit and security investigation events",
    description=(
        "List immutable audit events for the active tenant organization. "
        "Optional filters use logical AND and exact matching. "
        "Time range semantics: occurred_from <= occurred_at < occurred_to. "
        "Taxonomy event names are validated through the security event registry. "
        "Requires audit:read."
    ),
    responses={
        **success_response(model=AuditEventListResponse, description="Audit events returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_audit_events(
    tenant_context: Annotated[TenantContext, Depends(require_permission(AUDIT_READ))],
    handler: Annotated[ListAuditEventsHandler, Depends(get_list_audit_events_handler)],
    params: Annotated[
        AuditEventInvestigationParams,
        Depends(get_audit_event_investigation_params),
    ],
) -> AuditEventListResponse:
    result = handler.handle(
        ListAuditEventsQuery(
            scope_organization_id=tenant_context.organization_id,
            offset=params.offset,
            limit=params.limit,
            event_name=params.event_name,
            event_category=params.event_category,
            severity=params.severity,
            action=params.action,
            resource_type=params.resource_type,
            resource_id=params.resource_id,
            actor_user_id=params.actor_user_id,
            outcome=params.outcome,
            target_organization_id=params.target_organization_id,
            request_id=params.request_id,
            occurred_from=params.occurred_from,
            occurred_to=params.occurred_to,
            sort_ascending=params.sort_ascending,
        )
    )
    return to_audit_event_list_response(result)


@router.get(
    "/integrity",
    response_model=AuditChainIntegrityResponse,
    operation_id=VERIFY_AUDIT_CHAIN_INTEGRITY,
    summary="Verify tenant audit integrity chain",
    description=(
        "Recalculate and verify the tamper-evident integrity chain for the active "
        "tenant organization. Read-only; does not mutate audit history. "
        "Requires audit:read."
    ),
    responses={
        **success_response(
            model=AuditChainIntegrityResponse,
            description="Integrity verification result.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def verify_audit_chain_integrity(
    tenant_context: Annotated[TenantContext, Depends(require_permission(AUDIT_READ))],
    handler: Annotated[VerifyAuditChainHandler, Depends(get_verify_audit_chain_handler)],
) -> AuditChainIntegrityResponse:
    result = handler.handle(
        VerifyAuditChainQuery(organization_id=tenant_context.organization_id)
    )
    return to_audit_chain_integrity_response(result)


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

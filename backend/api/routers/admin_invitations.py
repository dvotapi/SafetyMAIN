from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_clock,
    get_create_invitation_handler,
    get_get_invitation_handler,
    get_invitation_id,
    get_list_invitations_handler,
    get_reissue_invitation_handler,
    get_revoke_invitation_handler,
    require_permission,
)
from backend.api.mappers.admin_invitations import (
    to_create_invitation_response,
    to_invitation_list_response,
    to_invitation_response,
    to_reissue_invitation_response,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    CREATE_INVITATION,
    GET_INVITATION,
    LIST_INVITATIONS,
    REISSUE_INVITATION,
    REVOKE_INVITATION,
)
from backend.api.schemas.admin_invitations import (
    CreateInvitationRequest,
    CreateInvitationResponse,
    InvitationListResponse,
    InvitationResponse,
    ReissueInvitationResponse,
)
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import (
    INVITATION_READ,
    INVITATION_WRITE,
)
from backend.core.application.commands.invitation_lifecycle import (
    CreateInvitationCommand,
    ReissueInvitationCommand,
    RevokeInvitationCommand,
)
from backend.core.application.handlers.create_invitation import CreateInvitationHandler
from backend.core.application.handlers.get_invitation import GetInvitationHandler
from backend.core.application.handlers.invitation_lifecycle import (
    ReissueInvitationHandler,
    RevokeInvitationHandler,
)
from backend.core.application.handlers.list_invitations import ListInvitationsHandler
from backend.core.application.queries.invitations import GetInvitationQuery, ListInvitationsQuery
from backend.core.contracts.clock import ClockContract
from backend.core.domain.entities.invitation import InvitationStatus
from backend.core.domain.value_objects import InvitationId, OrganizationId, Role

router = APIRouter(prefix="/admin/invitations", tags=["Admin Invitations"])


@router.post(
    "",
    response_model=CreateInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_INVITATION,
    summary="Create an invitation",
    responses={
        **created_response(model=CreateInvitationResponse, description="Invitation created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_invitation(
    request_body: CreateInvitationRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(INVITATION_WRITE))],
    handler: Annotated[CreateInvitationHandler, Depends(get_create_invitation_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
) -> JSONResponse:
    assert tenant_context.actor_user_id is not None
    result = handler.handle(
        CreateInvitationCommand(
            organization_id=OrganizationId(value=request_body.organization_id),
            email=request_body.email,
            role=Role(value=request_body.role),
            created_by=tenant_context.actor_user_id,
            expires_at=request_body.expires_at,
        )
    )
    response_body = to_create_invitation_response(
        result.invitation,
        token=result.token,
        now=clock.now(),
    )
    location = f"{API_V1_PREFIX}/admin/invitations/{result.invitation.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=InvitationListResponse,
    operation_id=LIST_INVITATIONS,
    summary="List invitations",
    responses={
        **success_response(model=InvitationListResponse, description="Invitations returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_invitations(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(INVITATION_READ))],
    handler: Annotated[ListInvitationsHandler, Depends(get_list_invitations_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
    organization_id: Annotated[UUID, Query()],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    email: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    status: Annotated[InvitationStatus | None, Query()] = None,
    sort_ascending: Annotated[bool, Query()] = False,
) -> InvitationListResponse:
    result = handler.handle(
        ListInvitationsQuery(
            organization_id=OrganizationId(value=organization_id),
            offset=offset,
            limit=limit,
            email=email,
            role=Role(value=role) if role is not None else None,
            status=status,
            sort_ascending=sort_ascending,
        )
    )
    return to_invitation_list_response(result, now=clock.now())


@router.get(
    "/{invitation_id}",
    response_model=InvitationResponse,
    operation_id=GET_INVITATION,
    summary="Get an invitation",
    responses={
        **success_response(model=InvitationResponse, description="Invitation returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_invitation(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(INVITATION_READ))],
    invitation_id: Annotated[InvitationId, Depends(get_invitation_id)],
    handler: Annotated[GetInvitationHandler, Depends(get_get_invitation_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
) -> InvitationResponse:
    invitation = handler.handle(GetInvitationQuery(invitation_id=invitation_id))
    return to_invitation_response(invitation, now=clock.now())


@router.post(
    "/{invitation_id}/revoke",
    response_model=InvitationResponse,
    operation_id=REVOKE_INVITATION,
    summary="Revoke an invitation",
    responses={
        **success_response(model=InvitationResponse, description="Invitation revoked."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def revoke_invitation(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(INVITATION_WRITE))],
    invitation_id: Annotated[InvitationId, Depends(get_invitation_id)],
    handler: Annotated[RevokeInvitationHandler, Depends(get_revoke_invitation_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
) -> InvitationResponse:
    invitation = handler.handle(RevokeInvitationCommand(invitation_id=invitation_id))
    return to_invitation_response(invitation, now=clock.now())


@router.post(
    "/{invitation_id}/reissue",
    response_model=ReissueInvitationResponse,
    operation_id=REISSUE_INVITATION,
    summary="Reissue an invitation token",
    responses={
        **success_response(
            model=ReissueInvitationResponse,
            description="Invitation token reissued.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def reissue_invitation(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(INVITATION_WRITE))],
    invitation_id: Annotated[InvitationId, Depends(get_invitation_id)],
    handler: Annotated[ReissueInvitationHandler, Depends(get_reissue_invitation_handler)],
    clock: Annotated[ClockContract, Depends(get_clock)],
) -> ReissueInvitationResponse:
    result = handler.handle(ReissueInvitationCommand(invitation_id=invitation_id))
    return to_reissue_invitation_response(
        result.invitation,
        token=result.token,
        now=clock.now(),
    )

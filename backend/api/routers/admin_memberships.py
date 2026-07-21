from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_activate_membership_handler,
    get_create_membership_handler,
    get_deactivate_membership_handler,
    get_get_membership_handler,
    get_list_memberships_handler,
    get_membership_authorization_context,
    get_membership_id,
    get_update_membership_role_handler,
    require_permission,
)
from backend.api.mappers.admin_memberships import (
    to_membership_list_response,
    to_membership_response,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ACTIVATE_MEMBERSHIP,
    CREATE_MEMBERSHIP,
    DEACTIVATE_MEMBERSHIP,
    GET_MEMBERSHIP,
    LIST_MEMBERSHIPS,
    UPDATE_MEMBERSHIP_ROLE,
)
from backend.api.schemas.admin_memberships import (
    CreateMembershipRequest,
    MembershipListResponse,
    MembershipResponse,
    UpdateMembershipRoleRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    MEMBERSHIP_READ,
    MEMBERSHIP_WRITE,
)
from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.application.commands.membership_lifecycle import (
    ActivateMembershipCommand,
    DeactivateMembershipCommand,
)
from backend.core.application.commands.update_membership_role import UpdateMembershipRoleCommand
from backend.core.application.handlers.create_membership import CreateMembershipHandler
from backend.core.application.handlers.get_membership import GetMembershipHandler
from backend.core.application.handlers.list_memberships import ListMembershipsHandler
from backend.core.application.handlers.membership_lifecycle import (
    ActivateMembershipHandler,
    DeactivateMembershipHandler,
)
from backend.core.application.handlers.update_membership_role import UpdateMembershipRoleHandler
from backend.core.application.policies.membership_administration import (
    MembershipAuthorizationContext,
)
from backend.core.application.queries.get_membership import GetMembershipQuery
from backend.core.application.queries.list_memberships import ListMembershipsQuery
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId

router = APIRouter(prefix="/admin/memberships", tags=["Admin Memberships"])


@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_MEMBERSHIP,
    summary="Create a membership",
    responses={
        **created_response(model=MembershipResponse, description="Membership created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_membership(
    request_body: CreateMembershipRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_WRITE))],
    handler: Annotated[CreateMembershipHandler, Depends(get_create_membership_handler)],
) -> JSONResponse:
    membership = handler.handle(
        CreateMembershipCommand(
            user_id=UserId(value=request_body.user_id),
            organization_id=OrganizationId(value=request_body.organization_id),
            role=Role(value=request_body.role),
            is_active=request_body.is_active,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    response_body = to_membership_response(membership)
    location = f"{API_V1_PREFIX}/admin/memberships/{membership.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=MembershipListResponse,
    operation_id=LIST_MEMBERSHIPS,
    summary="List memberships",
    responses={
        **success_response(model=MembershipListResponse, description="Memberships returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_memberships(
    _tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_READ))],
    handler: Annotated[ListMembershipsHandler, Depends(get_list_memberships_handler)],
    organization_id: Annotated[UUID, Query()],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user_id: Annotated[UUID | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    sort_ascending: Annotated[bool, Query(alias="sort_asc")] = False,
) -> MembershipListResponse:
    parsed_role = Role(value=role) if role is not None else None
    result = handler.handle(
        ListMembershipsQuery(
            organization_id=OrganizationId(value=organization_id),
            offset=offset,
            limit=limit,
            user_id=UserId(value=user_id) if user_id is not None else None,
            role=parsed_role,
            is_active=is_active,
            sort_ascending=sort_ascending,
        )
    )
    return to_membership_list_response(result)


@router.get(
    "/{membership_id}",
    response_model=MembershipResponse,
    operation_id=GET_MEMBERSHIP,
    summary="Get a membership",
    responses={
        **success_response(model=MembershipResponse, description="Membership returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_membership(
    membership_id: Annotated[MembershipId, Depends(get_membership_id)],
    _tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_READ))],
    handler: Annotated[GetMembershipHandler, Depends(get_get_membership_handler)],
) -> MembershipResponse:
    membership = handler.handle(GetMembershipQuery(membership_id=membership_id))
    return to_membership_response(membership)


@router.patch(
    "/{membership_id}/role",
    response_model=MembershipResponse,
    operation_id=UPDATE_MEMBERSHIP_ROLE,
    summary="Update membership role",
    responses={
        **success_response(model=MembershipResponse, description="Membership role updated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_membership_role(
    request_body: UpdateMembershipRoleRequest,
    membership_id: Annotated[MembershipId, Depends(get_membership_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_WRITE))],
    authorization: Annotated[
        MembershipAuthorizationContext,
        Depends(get_membership_authorization_context),
    ],
    handler: Annotated[
        UpdateMembershipRoleHandler,
        Depends(get_update_membership_role_handler),
    ],
) -> MembershipResponse:
    membership = handler.handle(
        UpdateMembershipRoleCommand(
            membership_id=membership_id,
            role=Role(value=request_body.role),
            authorization=authorization,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_membership_response(membership)


@router.post(
    "/{membership_id}/activate",
    response_model=MembershipResponse,
    operation_id=ACTIVATE_MEMBERSHIP,
    summary="Activate a membership",
    responses={
        **success_response(model=MembershipResponse, description="Membership activated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def activate_membership(
    membership_id: Annotated[MembershipId, Depends(get_membership_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_WRITE))],
    handler: Annotated[ActivateMembershipHandler, Depends(get_activate_membership_handler)],
) -> MembershipResponse:
    membership = handler.handle(
        ActivateMembershipCommand(
            membership_id=membership_id,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_membership_response(membership)


@router.post(
    "/{membership_id}/deactivate",
    response_model=MembershipResponse,
    operation_id=DEACTIVATE_MEMBERSHIP,
    summary="Deactivate a membership",
    responses={
        **success_response(model=MembershipResponse, description="Membership deactivated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def deactivate_membership(
    membership_id: Annotated[MembershipId, Depends(get_membership_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(MEMBERSHIP_WRITE))],
    authorization: Annotated[
        MembershipAuthorizationContext,
        Depends(get_membership_authorization_context),
    ],
    handler: Annotated[
        DeactivateMembershipHandler,
        Depends(get_deactivate_membership_handler),
    ],
) -> MembershipResponse:
    membership = handler.handle(
        DeactivateMembershipCommand(
            membership_id=membership_id,
            authorization=authorization,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_membership_response(membership)

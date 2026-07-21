from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_activate_organization_handler,
    get_create_organization_handler,
    get_deactivate_organization_handler,
    get_get_organization_handler,
    get_list_organizations_handler,
    get_target_organization_id,
    get_update_organization_handler,
    require_permission,
)
from backend.api.mappers.admin_organizations import (
    to_organization_list_response,
    to_organization_response,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ACTIVATE_ORGANIZATION,
    CREATE_ORGANIZATION,
    DEACTIVATE_ORGANIZATION,
    GET_ORGANIZATION,
    LIST_ORGANIZATIONS,
    UPDATE_ORGANIZATION,
)
from backend.api.schemas.admin_organizations import (
    CreateOrganizationRequest,
    OrganizationListResponse,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from backend.api.security import TenantContext
from backend.core.application.authorization.policies.resource_permissions import (
    ORGANIZATION_READ,
    ORGANIZATION_WRITE,
)
from backend.core.application.commands.create_organization import CreateOrganizationCommand
from backend.core.application.commands.organization_lifecycle import (
    ActivateOrganizationCommand,
    DeactivateOrganizationCommand,
)
from backend.core.application.commands.update_organization import UpdateOrganizationCommand
from backend.core.application.handlers.create_organization import CreateOrganizationHandler
from backend.core.application.handlers.get_organization import GetOrganizationHandler
from backend.core.application.handlers.list_organizations import ListOrganizationsHandler
from backend.core.application.handlers.organization_lifecycle import (
    ActivateOrganizationHandler,
    DeactivateOrganizationHandler,
)
from backend.core.application.handlers.update_organization import UpdateOrganizationHandler
from backend.core.application.queries.get_organization import GetOrganizationQuery
from backend.core.application.queries.list_organizations import ListOrganizationsQuery
from backend.core.domain.value_objects import OrganizationId

router = APIRouter(prefix="/admin/organizations", tags=["Admin Organizations"])


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_ORGANIZATION,
    summary="Create an organization",
    responses={
        **created_response(model=OrganizationResponse, description="Organization created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_organization(
    request_body: CreateOrganizationRequest,
    _tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_WRITE)),
    ],
    handler: Annotated[CreateOrganizationHandler, Depends(get_create_organization_handler)],
) -> JSONResponse:
    organization = handler.handle(
        CreateOrganizationCommand(
            name=request_body.name,
            is_active=request_body.is_active,
        )
    )
    response_body = to_organization_response(organization)
    location = f"{API_V1_PREFIX}/admin/organizations/{organization.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=OrganizationListResponse,
    operation_id=LIST_ORGANIZATIONS,
    summary="List organizations",
    responses={
        **success_response(
            model=OrganizationListResponse,
            description="Organizations returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_organizations(
    _tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_READ)),
    ],
    handler: Annotated[ListOrganizationsHandler, Depends(get_list_organizations_handler)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    is_active: Annotated[bool | None, Query()] = None,
    name: Annotated[str | None, Query(max_length=255)] = None,
    sort_ascending: Annotated[bool, Query(alias="sort_asc")] = False,
) -> OrganizationListResponse:
    result = handler.handle(
        ListOrganizationsQuery(
            offset=offset,
            limit=limit,
            is_active=is_active,
            name=name,
            sort_ascending=sort_ascending,
        )
    )
    return to_organization_list_response(result)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    operation_id=GET_ORGANIZATION,
    summary="Get an organization",
    responses={
        **success_response(model=OrganizationResponse, description="Organization returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_organization(
    organization_id: Annotated[OrganizationId, Depends(get_target_organization_id)],
    _tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_READ)),
    ],
    handler: Annotated[GetOrganizationHandler, Depends(get_get_organization_handler)],
) -> OrganizationResponse:
    organization = handler.handle(
        GetOrganizationQuery(organization_id=organization_id)
    )
    return to_organization_response(organization)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    operation_id=UPDATE_ORGANIZATION,
    summary="Update an organization",
    responses={
        **success_response(model=OrganizationResponse, description="Organization updated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_organization(
    request_body: UpdateOrganizationRequest,
    organization_id: Annotated[OrganizationId, Depends(get_target_organization_id)],
    _tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_WRITE)),
    ],
    handler: Annotated[UpdateOrganizationHandler, Depends(get_update_organization_handler)],
) -> OrganizationResponse:
    organization = handler.handle(
        UpdateOrganizationCommand(
            organization_id=organization_id,
            name=request_body.name,
        )
    )
    return to_organization_response(organization)


@router.post(
    "/{organization_id}/activate",
    response_model=OrganizationResponse,
    operation_id=ACTIVATE_ORGANIZATION,
    summary="Activate an organization",
    responses={
        **success_response(model=OrganizationResponse, description="Organization activated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def activate_organization(
    organization_id: Annotated[OrganizationId, Depends(get_target_organization_id)],
    _tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_WRITE)),
    ],
    handler: Annotated[
        ActivateOrganizationHandler,
        Depends(get_activate_organization_handler),
    ],
) -> OrganizationResponse:
    organization = handler.handle(
        ActivateOrganizationCommand(organization_id=organization_id)
    )
    return to_organization_response(organization)


@router.post(
    "/{organization_id}/deactivate",
    response_model=OrganizationResponse,
    operation_id=DEACTIVATE_ORGANIZATION,
    summary="Deactivate an organization",
    responses={
        **success_response(
            model=OrganizationResponse,
            description="Organization deactivated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def deactivate_organization(
    organization_id: Annotated[OrganizationId, Depends(get_target_organization_id)],
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(ORGANIZATION_WRITE)),
    ],
    handler: Annotated[
        DeactivateOrganizationHandler,
        Depends(get_deactivate_organization_handler),
    ],
) -> OrganizationResponse:
    organization = handler.handle(
        DeactivateOrganizationCommand(
            organization_id=organization_id,
            authorization_organization_id=tenant_context.organization_id,
        )
    )
    return to_organization_response(organization)

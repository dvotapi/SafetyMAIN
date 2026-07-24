from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_activate_hazard_handler,
    get_archive_hazard_handler,
    get_create_hazard_handler,
    get_get_hazard_handler,
    get_hazard_id,
    get_list_hazards_handler,
    get_restore_hazard_handler,
    get_update_hazard_handler,
    require_permission,
)
from backend.api.mappers.hazards import to_hazard_list_response, to_hazard_response
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ACTIVATE_HAZARD,
    ARCHIVE_HAZARD,
    CREATE_HAZARD,
    GET_HAZARD,
    LIST_HAZARDS,
    RESTORE_HAZARD,
    UPDATE_HAZARD,
)
from backend.api.schemas.hazards import (
    ArchiveHazardRequest,
    CreateHazardRequest,
    HazardLifecycleRequest,
    HazardListResponse,
    HazardResponse,
    RestoreHazardRequest,
    UpdateHazardRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    HAZARD_ACTIVATE,
    HAZARD_ARCHIVE,
    HAZARD_CREATE,
    HAZARD_READ,
    HAZARD_RESTORE,
    HAZARD_UPDATE,
)
from backend.core.application.commands.hazard_lifecycle import (
    ActivateHazardCommand,
    ArchiveHazardCommand,
    CreateHazardCommand,
    RestoreHazardCommand,
    UpdateHazardCommand,
)
from backend.core.application.handlers.create_hazard import CreateHazardHandler
from backend.core.application.handlers.get_list_hazards import (
    GetHazardHandler,
    ListHazardsHandler,
)
from backend.core.application.handlers.hazard_lifecycle import (
    ActivateHazardHandler,
    ArchiveHazardHandler,
    RestoreHazardHandler,
)
from backend.core.application.handlers.update_hazard import UpdateHazardHandler
from backend.core.application.queries.hazards import GetHazardQuery, ListHazardsQuery
from backend.core.domain.value_objects.safety_enums import (
    AffectedSubject,
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)
from backend.core.domain.value_objects.safety_ids import HazardId

router = APIRouter(prefix="/hazards", tags=["Hazards"])


@router.post(
    "",
    response_model=HazardResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_HAZARD,
    summary="Create a hazard",
    responses={
        **created_response(model=HazardResponse, description="Hazard created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_hazard(
    request_body: CreateHazardRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(HAZARD_CREATE))],
    handler: Annotated[CreateHazardHandler, Depends(get_create_hazard_handler)],
) -> JSONResponse:
    assert tenant_context.actor_user_id is not None
    hazard = handler.handle(
        CreateHazardCommand(
            organization_id=tenant_context.organization_id,
            actor_id=tenant_context.actor_user_id,
            code=request_body.code,
            title=request_body.title,
            description=request_body.description,
            category=HazardCategory(request_body.category),
            safety_directions=tuple(
                SafetyDirection(direction)
                for direction in request_body.safety_directions
            ),
            source=HazardSource(request_body.source),
            affected_subjects=tuple(
                AffectedSubject(subject)
                for subject in request_body.affected_subjects
            ),
            location_reference=request_body.location_reference,
            process_reference=request_body.process_reference,
            equipment_reference=request_body.equipment_reference,
            extension_references=request_body.extension_references,
            identified_at=request_body.identified_at,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    response_body = to_hazard_response(hazard)
    location = f"{API_V1_PREFIX}/hazards/{hazard.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=HazardListResponse,
    operation_id=LIST_HAZARDS,
    summary="List hazards",
    responses={
        **success_response(model=HazardListResponse, description="Hazards returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_hazards(
    tenant_context: Annotated[TenantContext, Depends(require_permission(HAZARD_READ))],
    handler: Annotated[ListHazardsHandler, Depends(get_list_hazards_handler)],
    status_filter: Annotated[HazardStatus | None, Query(alias="status")] = None,
    category: Annotated[HazardCategory | None, Query()] = None,
    safety_direction: Annotated[SafetyDirection | None, Query()] = None,
    source: Annotated[HazardSource | None, Query()] = None,
    affected_subject: Annotated[AffectedSubject | None, Query()] = None,
    identified_from: Annotated[datetime | None, Query()] = None,
    identified_to: Annotated[datetime | None, Query()] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> HazardListResponse:
    page = handler.handle(
        ListHazardsQuery(
            organization_id=tenant_context.organization_id,
            status=status_filter,
            category=category,
            safety_direction=safety_direction,
            source=source,
            affected_subject=affected_subject,
            identified_from=identified_from,
            identified_to=identified_to,
            created_from=created_from,
            created_to=created_to,
            search=search,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )
    )
    return to_hazard_list_response(page)


@router.get(
    "/{hazard_id}",
    response_model=HazardResponse,
    operation_id=GET_HAZARD,
    summary="Get a hazard",
    responses={
        **success_response(model=HazardResponse, description="Hazard returned."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_hazard(
    hazard_id: Annotated[HazardId, Depends(get_hazard_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(HAZARD_READ))],
    handler: Annotated[GetHazardHandler, Depends(get_get_hazard_handler)],
) -> HazardResponse:
    hazard = handler.handle(
        GetHazardQuery(
            organization_id=tenant_context.organization_id,
            hazard_id=hazard_id,
        )
    )
    return to_hazard_response(hazard)


@router.patch(
    "/{hazard_id}",
    response_model=HazardResponse,
    operation_id=UPDATE_HAZARD,
    summary="Update a hazard",
    responses={
        **success_response(model=HazardResponse, description="Hazard updated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_hazard(
    hazard_id: Annotated[HazardId, Depends(get_hazard_id)],
    request_body: UpdateHazardRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(HAZARD_UPDATE))],
    handler: Annotated[UpdateHazardHandler, Depends(get_update_hazard_handler)],
) -> HazardResponse:
    assert tenant_context.actor_user_id is not None
    fields_set = request_body.model_fields_set
    hazard = handler.handle(
        UpdateHazardCommand(
            organization_id=tenant_context.organization_id,
            hazard_id=hazard_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            title=request_body.title,
            description=request_body.description,
            category=(
                None
                if request_body.category is None
                else HazardCategory(request_body.category)
            ),
            safety_directions=(
                None
                if request_body.safety_directions is None
                else tuple(
                    SafetyDirection(direction)
                    for direction in request_body.safety_directions
                )
            ),
            source=(
                None
                if request_body.source is None
                else HazardSource(request_body.source)
            ),
            affected_subjects=(
                None
                if request_body.affected_subjects is None
                else tuple(
                    AffectedSubject(subject)
                    for subject in request_body.affected_subjects
                )
            ),
            location_reference=(
                request_body.location_reference
                if "location_reference" in fields_set
                else ...
            ),
            process_reference=(
                request_body.process_reference
                if "process_reference" in fields_set
                else ...
            ),
            equipment_reference=(
                request_body.equipment_reference
                if "equipment_reference" in fields_set
                else ...
            ),
            extension_references=request_body.extension_references,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_hazard_response(hazard)


@router.post(
    "/{hazard_id}/activate",
    response_model=HazardResponse,
    operation_id=ACTIVATE_HAZARD,
    summary="Activate a hazard",
    responses={
        **success_response(model=HazardResponse, description="Hazard activated."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def activate_hazard(
    hazard_id: Annotated[HazardId, Depends(get_hazard_id)],
    request_body: HazardLifecycleRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(HAZARD_ACTIVATE))
    ],
    handler: Annotated[ActivateHazardHandler, Depends(get_activate_hazard_handler)],
) -> HazardResponse:
    assert tenant_context.actor_user_id is not None
    hazard = handler.handle(
        ActivateHazardCommand(
            organization_id=tenant_context.organization_id,
            hazard_id=hazard_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_hazard_response(hazard)


@router.post(
    "/{hazard_id}/archive",
    response_model=HazardResponse,
    operation_id=ARCHIVE_HAZARD,
    summary="Archive a hazard",
    responses={
        **success_response(model=HazardResponse, description="Hazard archived."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def archive_hazard(
    hazard_id: Annotated[HazardId, Depends(get_hazard_id)],
    request_body: ArchiveHazardRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(HAZARD_ARCHIVE))
    ],
    handler: Annotated[ArchiveHazardHandler, Depends(get_archive_hazard_handler)],
) -> HazardResponse:
    assert tenant_context.actor_user_id is not None
    hazard = handler.handle(
        ArchiveHazardCommand(
            organization_id=tenant_context.organization_id,
            hazard_id=hazard_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_hazard_response(hazard)


@router.post(
    "/{hazard_id}/restore",
    response_model=HazardResponse,
    operation_id=RESTORE_HAZARD,
    summary="Restore an archived hazard",
    responses={
        **success_response(model=HazardResponse, description="Hazard restored."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def restore_hazard(
    hazard_id: Annotated[HazardId, Depends(get_hazard_id)],
    request_body: RestoreHazardRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(HAZARD_RESTORE))
    ],
    handler: Annotated[RestoreHazardHandler, Depends(get_restore_hazard_handler)],
) -> HazardResponse:
    assert tenant_context.actor_user_id is not None
    hazard = handler.handle(
        RestoreHazardCommand(
            organization_id=tenant_context.organization_id,
            hazard_id=hazard_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_hazard_response(hazard)

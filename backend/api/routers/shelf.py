"""Document shelf API (TASK-P11-012 §2.5, docs/api/ShelfAPI.md).

No DELETE routes: places, sections and documents are never removed; unlinking
a document is an audited POST command.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_bulk_exclude_shelf_slots_handler,
    get_confirm_shelf_slot_applicable_handler,
    get_create_shelf_slot_handler,
    get_develop_shelf_slot_document_handler,
    get_exclude_shelf_slot_handler,
    get_get_shelf_overview_handler,
    get_get_shelf_section_slots_handler,
    get_get_shelf_slot_handler,
    get_link_shelf_slot_document_handler,
    get_restore_shelf_slot_handler,
    get_search_shelf_slots_handler,
    get_shelf_capabilities,
    get_shelf_slot_id,
    get_unlink_shelf_slot_document_handler,
    get_update_shelf_slot_handler,
    require_permission,
)
from backend.api.mappers.shelf import (
    to_develop_response,
    to_legal_basis,
    to_overview_response,
    to_section_slots_response,
    to_slot_detail_response,
    to_slot_list_response,
    update_changes,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    BULK_EXCLUDE_SHELF_SLOTS,
    CONFIRM_SHELF_SLOT_APPLICABLE,
    CREATE_SHELF_SLOT,
    DEVELOP_SHELF_SLOT_DOCUMENT,
    EXCLUDE_SHELF_SLOT,
    GET_SHELF_OVERVIEW,
    GET_SHELF_SLOT,
    LINK_SHELF_SLOT_DOCUMENT,
    LIST_SHELF_SECTION_SLOTS,
    RESTORE_SHELF_SLOT,
    SEARCH_SHELF_SLOTS,
    UNLINK_SHELF_SLOT_DOCUMENT,
    UPDATE_SHELF_SLOT,
)
from backend.api.schemas.shelf import (
    BulkExcludeShelfSlotsRequest,
    CreateShelfSlotRequest,
    DevelopShelfSlotRequest,
    DevelopShelfSlotResponse,
    ExcludeShelfSlotRequest,
    LinkShelfSlotDocumentRequest,
    ShelfOverviewResponse,
    ShelfSectionSlotsResponse,
    ShelfSlotDetailResponse,
    ShelfSlotListResponse,
    ShelfSlotVersionRequest,
    UpdateShelfSlotRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    COMPLIANCE_DOCUMENT_CREATE,
    COMPLIANCE_DOCUMENT_READ,
    SHELF_CURATE,
    SHELF_READ,
)
from backend.core.application.commands.shelf import (
    BulkExcludeShelfSlotsCommand,
    ConfirmShelfSlotApplicableCommand,
    CreateShelfSlotCommand,
    DevelopShelfSlotDocumentCommand,
    ExcludeShelfSlotCommand,
    LinkShelfSlotDocumentCommand,
    RestoreShelfSlotCommand,
    UnlinkShelfSlotDocumentCommand,
    UpdateShelfSlotCommand,
)
from backend.core.application.exceptions.authentication import UnauthenticatedError
from backend.core.application.handlers.shelf import (
    BulkExcludeShelfSlotsHandler,
    ConfirmShelfSlotApplicableHandler,
    CreateShelfSlotHandler,
    DevelopShelfSlotDocumentHandler,
    ExcludeShelfSlotHandler,
    GetShelfOverviewHandler,
    GetShelfSectionSlotsHandler,
    GetShelfSlotHandler,
    LinkShelfSlotDocumentHandler,
    RestoreShelfSlotHandler,
    SearchShelfSlotsHandler,
    UnlinkShelfSlotDocumentHandler,
    UpdateShelfSlotHandler,
)
from backend.core.application.queries.shelf import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_MAX_LIMIT,
    SEARCH_QUERY_MAX_LENGTH,
    GetShelfOverviewQuery,
    GetShelfSectionSlotsQuery,
    GetShelfSlotQuery,
    SearchShelfSlotsQuery,
    ShelfCapabilities,
)
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.safety_ids import (
    ComplianceDocumentId,
    ShelfSlotId,
)
from backend.core.domain.value_objects.shelf_enums import (
    CuratedSlotStatus,
    SlotExclusionReason,
    SlotKeptOn,
    SlotObligationLevel,
)

router = APIRouter(prefix="/shelf", tags=["Document Shelf"])

Reader = Annotated[TenantContext, Depends(require_permission(SHELF_READ))]
Curator = Annotated[TenantContext, Depends(require_permission(SHELF_CURATE))]
Capabilities = Annotated[ShelfCapabilities, Depends(get_shelf_capabilities)]
SlotIdParam = Annotated[ShelfSlotId, Depends(get_shelf_slot_id)]


def _actor(tenant_context: TenantContext) -> UserId:
    if tenant_context.actor_user_id is None:
        raise UnauthenticatedError()
    return tenant_context.actor_user_id


def _detail_responses(description: str) -> dict[int | str, dict[str, Any]]:
    return {
        **success_response(model=ShelfSlotDetailResponse, description=description),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    }


@router.get(
    "",
    response_model=ShelfOverviewResponse,
    operation_id=GET_SHELF_OVERVIEW,
    responses={
        **success_response(model=ShelfOverviewResponse, description="Shelf overview."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_shelf_overview(
    tenant_context: Reader,
    handler: Annotated[GetShelfOverviewHandler, Depends(get_get_shelf_overview_handler)],
) -> ShelfOverviewResponse:
    view = handler.handle(GetShelfOverviewQuery(organization_id=tenant_context.organization_id))
    return to_overview_response(view)


@router.get(
    "/sections/{section_code}/slots",
    response_model=ShelfSectionSlotsResponse,
    operation_id=LIST_SHELF_SECTION_SLOTS,
    responses={
        **success_response(
            model=ShelfSectionSlotsResponse, description="Places of one shelf by subsection."
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_shelf_section_slots(
    section_code: Annotated[str, Path(min_length=1, max_length=6)],
    tenant_context: Reader,
    handler: Annotated[
        GetShelfSectionSlotsHandler, Depends(get_get_shelf_section_slots_handler)
    ],
) -> ShelfSectionSlotsResponse:
    view = handler.handle(
        GetShelfSectionSlotsQuery(
            organization_id=tenant_context.organization_id, section_code=section_code
        )
    )
    return to_section_slots_response(view)


@router.get(
    "/slots",
    response_model=ShelfSlotListResponse,
    operation_id=SEARCH_SHELF_SLOTS,
    responses={
        **success_response(model=ShelfSlotListResponse, description="Matching places."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def search_shelf_slots(
    tenant_context: Reader,
    handler: Annotated[SearchShelfSlotsHandler, Depends(get_search_shelf_slots_handler)],
    q: Annotated[str, Query(min_length=1, max_length=SEARCH_QUERY_MAX_LENGTH)],
    limit: Annotated[int, Query(ge=1, le=SEARCH_MAX_LIMIT)] = SEARCH_DEFAULT_LIMIT,
) -> ShelfSlotListResponse:
    views = handler.handle(
        SearchShelfSlotsQuery(
            organization_id=tenant_context.organization_id, query=q, limit=limit
        )
    )
    return to_slot_list_response(views)


@router.get(
    "/slots/{slot_id}",
    response_model=ShelfSlotDetailResponse,
    operation_id=GET_SHELF_SLOT,
    responses=_detail_responses("Place detail."),
)
def get_shelf_slot(
    slot_id: SlotIdParam,
    tenant_context: Reader,
    capabilities: Capabilities,
    handler: Annotated[GetShelfSlotHandler, Depends(get_get_shelf_slot_handler)],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        GetShelfSlotQuery(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            capabilities=capabilities,
        )
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots",
    response_model=ShelfSlotDetailResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_SHELF_SLOT,
    responses={
        **created_response(model=ShelfSlotDetailResponse, description="Place created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_shelf_slot(
    request_body: CreateShelfSlotRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[CreateShelfSlotHandler, Depends(get_create_shelf_slot_handler)],
) -> JSONResponse:
    view = handler.handle(
        CreateShelfSlotCommand(
            organization_id=tenant_context.organization_id,
            actor_id=_actor(tenant_context),
            code=request_body.code,
            title=request_body.title,
            short_title=request_body.short_title,
            document_kind=request_body.document_kind,
            kept_on=SlotKeptOn(request_body.kept_on),
            obligation_level=SlotObligationLevel(request_body.obligation_level),
            curated_status=CuratedSlotStatus(request_body.curated_status),
            applicability_condition=request_body.applicability_condition,
            legal_basis=to_legal_basis(request_body.legal_basis),
            review_cycle_text=request_body.review_cycle_text,
            review_period_months=request_body.review_period_months,
            document_type_code=request_body.document_type_code,
            proposed_document_type=request_body.proposed_document_type,
            responsible_text=request_body.responsible_text,
            legacy_location=request_body.legacy_location,
            notes=request_body.notes,
            package_code=request_body.package_code,
            legacy_code=request_body.legacy_code,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    body = to_slot_detail_response(view)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=body.model_dump(mode="json"),
        headers={"Location": f"{API_V1_PREFIX}/shelf/slots/{view.slot.id.value}"},
    )


@router.patch(
    "/slots/{slot_id}",
    response_model=ShelfSlotDetailResponse,
    operation_id=UPDATE_SHELF_SLOT,
    responses=_detail_responses("Place updated."),
)
def update_shelf_slot(
    slot_id: SlotIdParam,
    request_body: UpdateShelfSlotRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[UpdateShelfSlotHandler, Depends(get_update_shelf_slot_handler)],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        UpdateShelfSlotCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            changes=update_changes(request_body),
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/bulk-exclude",
    response_model=ShelfSlotListResponse,
    operation_id=BULK_EXCLUDE_SHELF_SLOTS,
    responses={
        **success_response(model=ShelfSlotListResponse, description="Places excluded."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def bulk_exclude_shelf_slots(
    request_body: BulkExcludeShelfSlotsRequest,
    tenant_context: Curator,
    handler: Annotated[
        BulkExcludeShelfSlotsHandler, Depends(get_bulk_exclude_shelf_slots_handler)
    ],
) -> ShelfSlotListResponse:
    views = handler.handle(
        BulkExcludeShelfSlotsCommand(
            organization_id=tenant_context.organization_id,
            actor_id=_actor(tenant_context),
            items=tuple(
                (ShelfSlotId(value=item.slot_id), item.version) for item in request_body.items
            ),
            reason=SlotExclusionReason(request_body.reason),
            comment=request_body.comment,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_slot_list_response(views)


@router.post(
    "/slots/{slot_id}/exclude",
    response_model=ShelfSlotDetailResponse,
    operation_id=EXCLUDE_SHELF_SLOT,
    responses=_detail_responses("Place excluded."),
)
def exclude_shelf_slot(
    slot_id: SlotIdParam,
    request_body: ExcludeShelfSlotRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[ExcludeShelfSlotHandler, Depends(get_exclude_shelf_slot_handler)],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        ExcludeShelfSlotCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            reason=SlotExclusionReason(request_body.reason),
            comment=request_body.comment,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/{slot_id}/restore",
    response_model=ShelfSlotDetailResponse,
    operation_id=RESTORE_SHELF_SLOT,
    responses=_detail_responses("Place restored."),
)
def restore_shelf_slot(
    slot_id: SlotIdParam,
    request_body: ShelfSlotVersionRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[RestoreShelfSlotHandler, Depends(get_restore_shelf_slot_handler)],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        RestoreShelfSlotCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/{slot_id}/confirm-applicable",
    response_model=ShelfSlotDetailResponse,
    operation_id=CONFIRM_SHELF_SLOT_APPLICABLE,
    responses=_detail_responses("Place confirmed applicable."),
)
def confirm_shelf_slot_applicable(
    slot_id: SlotIdParam,
    request_body: ShelfSlotVersionRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[
        ConfirmShelfSlotApplicableHandler, Depends(get_confirm_shelf_slot_applicable_handler)
    ],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        ConfirmShelfSlotApplicableCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/{slot_id}/documents",
    response_model=ShelfSlotDetailResponse,
    operation_id=LINK_SHELF_SLOT_DOCUMENT,
    responses=_detail_responses("Document linked."),
)
def link_shelf_slot_document(
    slot_id: SlotIdParam,
    request_body: LinkShelfSlotDocumentRequest,
    tenant_context: Curator,
    _can_read_documents: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_READ))
    ],
    capabilities: Capabilities,
    handler: Annotated[
        LinkShelfSlotDocumentHandler, Depends(get_link_shelf_slot_document_handler)
    ],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        LinkShelfSlotDocumentCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            document_id=ComplianceDocumentId(value=request_body.document_id),
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/{slot_id}/documents/{document_id}/unlink",
    response_model=ShelfSlotDetailResponse,
    operation_id=UNLINK_SHELF_SLOT_DOCUMENT,
    responses=_detail_responses("Document unlinked."),
)
def unlink_shelf_slot_document(
    slot_id: SlotIdParam,
    document_id: Annotated[UUID, Path()],
    request_body: ShelfSlotVersionRequest,
    tenant_context: Curator,
    capabilities: Capabilities,
    handler: Annotated[
        UnlinkShelfSlotDocumentHandler, Depends(get_unlink_shelf_slot_document_handler)
    ],
) -> ShelfSlotDetailResponse:
    view = handler.handle(
        UnlinkShelfSlotDocumentCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            document_id=ComplianceDocumentId(value=document_id),
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    return to_slot_detail_response(view)


@router.post(
    "/slots/{slot_id}/develop",
    response_model=DevelopShelfSlotResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=DEVELOP_SHELF_SLOT_DOCUMENT,
    responses={
        **created_response(
            model=DevelopShelfSlotResponse, description="Draft document created and linked."
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def develop_shelf_slot_document(
    slot_id: SlotIdParam,
    request_body: DevelopShelfSlotRequest,
    tenant_context: Curator,
    _can_create_documents: Annotated[
        TenantContext, Depends(require_permission(COMPLIANCE_DOCUMENT_CREATE))
    ],
    capabilities: Capabilities,
    handler: Annotated[
        DevelopShelfSlotDocumentHandler, Depends(get_develop_shelf_slot_document_handler)
    ],
) -> JSONResponse:
    result = handler.handle(
        DevelopShelfSlotDocumentCommand(
            organization_id=tenant_context.organization_id,
            slot_id=slot_id,
            actor_id=_actor(tenant_context),
            expected_version=request_body.version,
            document_type_code=request_body.document_type_code,
            audit_context=AuditContext.from_tenant(tenant_context),
        ),
        capabilities=capabilities,
    )
    body = to_develop_response(result)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=body.model_dump(mode="json"),
        headers={
            "Location": f"{API_V1_PREFIX}/compliance-documents/{result.document.id.value}"
        },
    )

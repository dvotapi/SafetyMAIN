from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_add_risk_control_evidence_handler,
    get_archive_risk_control_handler,
    get_assign_risk_control_owner_handler,
    get_cancel_risk_control_handler,
    get_complete_risk_control_implementation_handler,
    get_complete_risk_control_review_handler,
    get_create_risk_control_handler,
    get_get_risk_control_handler,
    get_list_risk_controls_handler,
    get_materialize_risk_controls_handler,
    get_plan_risk_control_handler,
    get_record_risk_control_verification_handler,
    get_resume_risk_control_handler,
    get_risk_control_id,
    get_schedule_risk_control_review_handler,
    get_start_risk_control_implementation_handler,
    get_supersede_risk_control_handler,
    get_suspend_risk_control_handler,
    get_update_risk_control_handler,
    get_update_risk_control_progress_handler,
    require_permission,
)
from backend.api.mappers.risk_controls import (
    parse_evidence,
    parse_implementation,
    parse_owner,
    parse_review_schedule,
    parse_scope,
    parse_source,
    parse_verification,
    to_risk_control_list_response,
    to_risk_control_response,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    ADD_RISK_CONTROL_EVIDENCE,
    ARCHIVE_RISK_CONTROL,
    ASSIGN_RISK_CONTROL_OWNER,
    CANCEL_RISK_CONTROL,
    COMPLETE_RISK_CONTROL_IMPLEMENTATION,
    COMPLETE_RISK_CONTROL_REVIEW,
    CREATE_RISK_CONTROL,
    GET_RISK_CONTROL,
    LIST_RISK_CONTROLS,
    MATERIALIZE_RISK_ASSESSMENT_CONTROLS,
    PLAN_RISK_CONTROL,
    RECORD_RISK_CONTROL_VERIFICATION,
    RESUME_RISK_CONTROL,
    SCHEDULE_RISK_CONTROL_REVIEW,
    START_RISK_CONTROL_IMPLEMENTATION,
    SUPERSEDE_RISK_CONTROL,
    SUSPEND_RISK_CONTROL,
    UPDATE_RISK_CONTROL,
    UPDATE_RISK_CONTROL_PROGRESS,
)
from backend.api.schemas.risk_controls import (
    AssignOwnerRequest,
    CompleteImplementationRequest,
    CompleteReviewRequest,
    CreateRiskControlRequest,
    EvidenceRequest,
    MaterializeControlsRequest,
    MaterializeControlsResponse,
    PlanRiskControlRequest,
    ProgressRequest,
    ReasonVersionRequest,
    RiskControlListResponse,
    RiskControlResponse,
    ScheduleReviewRequest,
    SupersedeRequest,
    SuspendRequest,
    UpdateRiskControlRequest,
    VerificationRequest,
    VersionOnlyRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    RISK_CONTROL_ARCHIVE,
    RISK_CONTROL_ASSIGN,
    RISK_CONTROL_CANCEL,
    RISK_CONTROL_CREATE,
    RISK_CONTROL_IMPLEMENT,
    RISK_CONTROL_MATERIALIZE,
    RISK_CONTROL_READ,
    RISK_CONTROL_REVIEW,
    RISK_CONTROL_SUPERSEDE,
    RISK_CONTROL_SUSPEND,
    RISK_CONTROL_UPDATE,
    RISK_CONTROL_VERIFY,
)
from backend.core.application.commands.risk_control_lifecycle import (
    AddRiskControlEvidenceCommand,
    ArchiveRiskControlCommand,
    AssignRiskControlOwnerCommand,
    CancelRiskControlCommand,
    CompleteRiskControlImplementationCommand,
    CompleteRiskControlReviewCommand,
    CreateRiskControlCommand,
    MaterializeRiskAssessmentControlsCommand,
    PlanRiskControlCommand,
    RecordRiskControlVerificationCommand,
    ResumeRiskControlCommand,
    ScheduleRiskControlReviewCommand,
    StartRiskControlImplementationCommand,
    SupersedeRiskControlCommand,
    SuspendRiskControlCommand,
    UpdateRiskControlCommand,
    UpdateRiskControlProgressCommand,
)
from backend.core.application.handlers.create_risk_control import (
    CreateRiskControlHandler,
)
from backend.core.application.handlers.get_list_risk_controls import (
    GetRiskControlHandler,
    ListRiskControlsHandler,
)
from backend.core.application.handlers.materialize_risk_controls import (
    MaterializeRiskAssessmentControlsHandler,
)
from backend.core.application.handlers.risk_control_lifecycle import (
    AddRiskControlEvidenceHandler,
    ArchiveRiskControlHandler,
    AssignRiskControlOwnerHandler,
    CancelRiskControlHandler,
    CompleteRiskControlImplementationHandler,
    CompleteRiskControlReviewHandler,
    PlanRiskControlHandler,
    RecordRiskControlVerificationHandler,
    ResumeRiskControlHandler,
    ScheduleRiskControlReviewHandler,
    StartRiskControlImplementationHandler,
    SupersedeRiskControlHandler,
    SuspendRiskControlHandler,
    UpdateRiskControlHandler,
    UpdateRiskControlProgressHandler,
)
from backend.core.application.queries.risk_controls import (
    GetRiskControlQuery,
    ListRiskControlsQuery,
)
from backend.core.domain.value_objects.risk_control_components import SuspensionInfo
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlType,
    EffectivenessResult,
    RiskControlStatus,
)
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)

router = APIRouter(prefix="/risk-controls", tags=["Risk Controls"])
materialize_router = APIRouter(prefix="/risk-assessments", tags=["Risk Assessments"])


@router.post(
    "",
    response_model=RiskControlResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_RISK_CONTROL,
    responses={
        **created_response(model=RiskControlResponse, description="Risk control created."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_risk_control(
    request_body: CreateRiskControlRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_CREATE))],
    handler: Annotated[CreateRiskControlHandler, Depends(get_create_risk_control_handler)],
) -> JSONResponse:
    assert tenant_context.actor_user_id is not None
    from datetime import UTC

    stamp = datetime.now(UTC)
    owner = (
        None
        if request_body.owner is None
        else parse_owner(
            request_body.owner,
            actor_id=tenant_context.actor_user_id,
            at=stamp,
        )
    )
    control = handler.handle(
        CreateRiskControlCommand(
            organization_id=tenant_context.organization_id,
            actor_id=tenant_context.actor_user_id,
            code=request_body.code,
            title=request_body.title,
            description=request_body.description,
            hierarchy_level=ControlType(request_body.hierarchy_level),
            control_nature=ControlNature(request_body.control_nature),
            source=parse_source(request_body.source),
            scope=parse_scope(request_body.scope),
            hazard_id=(
                None
                if request_body.hazard_id is None
                else HazardId(value=request_body.hazard_id)
            ),
            risk_assessment_id=(
                None
                if request_body.risk_assessment_id is None
                else RiskAssessmentId(value=request_body.risk_assessment_id)
            ),
            owner=owner,
            implementation=(
                None
                if request_body.implementation is None
                else parse_implementation(request_body.implementation)
            ),
            review_schedule=(
                None
                if request_body.review_schedule is None
                else parse_review_schedule(request_body.review_schedule)
            ),
            extension_data=request_body.extension_data,
            verification_method_requirement=request_body.verification_method_requirement,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    body = to_risk_control_response(control)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=body.model_dump(mode="json"),
        headers={"Location": f"{API_V1_PREFIX}/risk-controls/{control.id.value}"},
    )


@router.get(
    "",
    response_model=RiskControlListResponse,
    operation_id=LIST_RISK_CONTROLS,
    responses={
        **success_response(
            model=RiskControlListResponse,
            description="Risk controls listed.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_risk_controls(
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_READ))],
    handler: Annotated[ListRiskControlsHandler, Depends(get_list_risk_controls_handler)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    hierarchy_level: str | None = None,
    control_nature: str | None = None,
    hazard_id: UUID | None = None,
    risk_assessment_id: UUID | None = None,
    owner_reference: str | None = None,
    latest_effectiveness_result: str | None = None,
    review_due_before: datetime | None = None,
    review_due_after: datetime | None = None,
    overdue_only: bool = False,
    awaiting_verification: bool = False,
    search: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> RiskControlListResponse:
    page = handler.handle(
        ListRiskControlsQuery(
            organization_id=tenant_context.organization_id,
            hazard_id=None if hazard_id is None else HazardId(value=hazard_id),
            risk_assessment_id=(
                None
                if risk_assessment_id is None
                else RiskAssessmentId(value=risk_assessment_id)
            ),
            status=None if status_filter is None else RiskControlStatus(status_filter),
            hierarchy_level=(
                None if hierarchy_level is None else ControlType(hierarchy_level)
            ),
            control_nature=(
                None if control_nature is None else ControlNature(control_nature)
            ),
            owner_reference=owner_reference,
            latest_effectiveness_result=(
                None
                if latest_effectiveness_result is None
                else EffectivenessResult(latest_effectiveness_result)
            ),
            review_due_before=review_due_before,
            review_due_after=review_due_after,
            overdue_only=overdue_only,
            awaiting_verification=awaiting_verification,
            search=search,
            offset=offset,
            limit=limit,
        )
    )
    return to_risk_control_list_response(page)


@router.get(
    "/{control_id}",
    response_model=RiskControlResponse,
    operation_id=GET_RISK_CONTROL,
    responses={
        **success_response(
            model=RiskControlResponse,
            description="Risk control retrieved.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_risk_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_READ))],
    handler: Annotated[GetRiskControlHandler, Depends(get_get_risk_control_handler)],
) -> RiskControlResponse:
    control = handler.handle(
        GetRiskControlQuery(
            organization_id=tenant_context.organization_id,
            control_id=control_id,
        )
    )
    return to_risk_control_response(control)


@router.patch(
    "/{control_id}",
    response_model=RiskControlResponse,
    operation_id=UPDATE_RISK_CONTROL,
    responses={
        **success_response(
            model=RiskControlResponse,
            description="Risk control updated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_risk_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: UpdateRiskControlRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_UPDATE))],
    handler: Annotated[UpdateRiskControlHandler, Depends(get_update_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    control = handler.handle(
        UpdateRiskControlCommand(
            organization_id=tenant_context.organization_id,
            control_id=control_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            title=request_body.title,
            description=request_body.description,
            hierarchy_level=(
                None
                if request_body.hierarchy_level is None
                else ControlType(request_body.hierarchy_level)
            ),
            control_nature=(
                None
                if request_body.control_nature is None
                else ControlNature(request_body.control_nature)
            ),
            scope=(
                None
                if request_body.scope is None
                else parse_scope(request_body.scope)
            ),
            verification_method_requirement=request_body.verification_method_requirement,
            implementation=(
                None
                if request_body.implementation is None
                else parse_implementation(request_body.implementation)
            ),
            extension_data=request_body.extension_data,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_risk_control_response(control)


def _lifecycle_response(control: object) -> RiskControlResponse:
    return to_risk_control_response(control)  # type: ignore[arg-type]


@router.post("/{control_id}/assign-owner", response_model=RiskControlResponse, operation_id=ASSIGN_RISK_CONTROL_OWNER)
def assign_owner(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: AssignOwnerRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_ASSIGN))],
    handler: Annotated[AssignRiskControlOwnerHandler, Depends(get_assign_risk_control_owner_handler)],
) -> RiskControlResponse:
    from datetime import UTC

    assert tenant_context.actor_user_id is not None
    control = handler.handle(
        AssignRiskControlOwnerCommand(
            organization_id=tenant_context.organization_id,
            control_id=control_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            owner=parse_owner(
                request_body.owner,
                actor_id=tenant_context.actor_user_id,
                at=datetime.now(UTC),
            ),
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_risk_control_response(control)


@router.post("/{control_id}/plan", response_model=RiskControlResponse, operation_id=PLAN_RISK_CONTROL)
def plan_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: PlanRiskControlRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_UPDATE))],
    handler: Annotated[PlanRiskControlHandler, Depends(get_plan_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            PlanRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                implementation=parse_implementation(request_body.implementation),
                verification_method_requirement=request_body.verification_method_requirement,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post(
    "/{control_id}/start-implementation",
    response_model=RiskControlResponse,
    operation_id=START_RISK_CONTROL_IMPLEMENTATION,
)
def start_implementation(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: VersionOnlyRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_IMPLEMENT))],
    handler: Annotated[
        StartRiskControlImplementationHandler,
        Depends(get_start_risk_control_implementation_handler),
    ],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            StartRiskControlImplementationCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/progress", response_model=RiskControlResponse, operation_id=UPDATE_RISK_CONTROL_PROGRESS)
def update_progress(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: ProgressRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_IMPLEMENT))],
    handler: Annotated[
        UpdateRiskControlProgressHandler, Depends(get_update_risk_control_progress_handler)
    ],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            UpdateRiskControlProgressCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                progress=request_body.progress,
                summary=request_body.summary,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/evidence", response_model=RiskControlResponse, operation_id=ADD_RISK_CONTROL_EVIDENCE)
def add_evidence(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: EvidenceRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_IMPLEMENT))],
    handler: Annotated[
        AddRiskControlEvidenceHandler, Depends(get_add_risk_control_evidence_handler)
    ],
) -> RiskControlResponse:
    from datetime import UTC

    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            AddRiskControlEvidenceCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                evidence=parse_evidence(
                    evidence_type=request_body.evidence_type,
                    external_reference=request_body.external_reference,
                    title=request_body.title,
                    description=request_body.description,
                    actor_id=tenant_context.actor_user_id,
                    at=datetime.now(UTC),
                    checksum=request_body.checksum,
                    metadata=request_body.metadata,
                ),
                allow_after_implemented=request_body.allow_after_implemented,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post(
    "/{control_id}/complete-implementation",
    response_model=RiskControlResponse,
    operation_id=COMPLETE_RISK_CONTROL_IMPLEMENTATION,
)
def complete_implementation(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: CompleteImplementationRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_IMPLEMENT))],
    handler: Annotated[
        CompleteRiskControlImplementationHandler,
        Depends(get_complete_risk_control_implementation_handler),
    ],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            CompleteRiskControlImplementationCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                summary=request_body.summary,
                evidence_waiver_reason=request_body.evidence_waiver_reason,
                allow_incomplete_milestones=request_body.allow_incomplete_milestones,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post(
    "/{control_id}/verifications",
    response_model=RiskControlResponse,
    operation_id=RECORD_RISK_CONTROL_VERIFICATION,
)
def record_verification(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: VerificationRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_VERIFY))],
    handler: Annotated[
        RecordRiskControlVerificationHandler,
        Depends(get_record_risk_control_verification_handler),
    ],
) -> RiskControlResponse:
    from datetime import UTC

    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            RecordRiskControlVerificationCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                verification=parse_verification(
                    request_body,
                    actor_id=tenant_context.actor_user_id,
                    at=datetime.now(UTC),
                ),
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post(
    "/{control_id}/schedule-review",
    response_model=RiskControlResponse,
    operation_id=SCHEDULE_RISK_CONTROL_REVIEW,
)
def schedule_review(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: ScheduleReviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_REVIEW))],
    handler: Annotated[
        ScheduleRiskControlReviewHandler, Depends(get_schedule_risk_control_review_handler)
    ],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            ScheduleRiskControlReviewCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                schedule=parse_review_schedule(request_body.schedule),
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post(
    "/{control_id}/complete-review",
    response_model=RiskControlResponse,
    operation_id=COMPLETE_RISK_CONTROL_REVIEW,
)
def complete_review(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: CompleteReviewRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_REVIEW))],
    handler: Annotated[
        CompleteRiskControlReviewHandler, Depends(get_complete_risk_control_review_handler)
    ],
) -> RiskControlResponse:
    from datetime import UTC

    assert tenant_context.actor_user_id is not None
    verification = None
    if request_body.verification is not None:
        verification = parse_verification(
            request_body.verification,
            actor_id=tenant_context.actor_user_id,
            at=datetime.now(UTC),
        )
    return to_risk_control_response(
        handler.handle(
            CompleteRiskControlReviewCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                verification=verification,
                next_review_date=request_body.next_review_date,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/suspend", response_model=RiskControlResponse, operation_id=SUSPEND_RISK_CONTROL)
def suspend_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: SuspendRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_SUSPEND))],
    handler: Annotated[SuspendRiskControlHandler, Depends(get_suspend_risk_control_handler)],
) -> RiskControlResponse:
    from datetime import UTC

    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            SuspendRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                suspension=SuspensionInfo(
                    reason=request_body.reason,
                    suspended_by=tenant_context.actor_user_id,
                    suspended_at=datetime.now(UTC),
                    expected_resolution_date=request_body.expected_resolution_date,
                ),
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/resume", response_model=RiskControlResponse, operation_id=RESUME_RISK_CONTROL)
def resume_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: VersionOnlyRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_SUSPEND))],
    handler: Annotated[ResumeRiskControlHandler, Depends(get_resume_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            ResumeRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/supersede", response_model=RiskControlResponse, operation_id=SUPERSEDE_RISK_CONTROL)
def supersede_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: SupersedeRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_SUPERSEDE))],
    handler: Annotated[SupersedeRiskControlHandler, Depends(get_supersede_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            SupersedeRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                replacement_control_id=RiskControlId(value=request_body.replacement_control_id),
                reason=request_body.reason,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/archive", response_model=RiskControlResponse, operation_id=ARCHIVE_RISK_CONTROL)
def archive_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: ReasonVersionRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_ARCHIVE))],
    handler: Annotated[ArchiveRiskControlHandler, Depends(get_archive_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            ArchiveRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                reason=request_body.reason,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@router.post("/{control_id}/cancel", response_model=RiskControlResponse, operation_id=CANCEL_RISK_CONTROL)
def cancel_control(
    control_id: Annotated[RiskControlId, Depends(get_risk_control_id)],
    request_body: ReasonVersionRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CONTROL_CANCEL))],
    handler: Annotated[CancelRiskControlHandler, Depends(get_cancel_risk_control_handler)],
) -> RiskControlResponse:
    assert tenant_context.actor_user_id is not None
    return to_risk_control_response(
        handler.handle(
            CancelRiskControlCommand(
                organization_id=tenant_context.organization_id,
                control_id=control_id,
                actor_id=tenant_context.actor_user_id,
                expected_version=request_body.expected_version,
                reason=request_body.reason,
                audit_context=AuditContext.from_tenant(tenant_context),
            )
        )
    )


@materialize_router.post(
    "/{assessment_id}/materialize-controls",
    response_model=MaterializeControlsResponse,
    operation_id=MATERIALIZE_RISK_ASSESSMENT_CONTROLS,
)
def materialize_controls(
    assessment_id: UUID,
    request_body: MaterializeControlsRequest,
    tenant_context: Annotated[
        TenantContext, Depends(require_permission(RISK_CONTROL_MATERIALIZE))
    ],
    handler: Annotated[
        MaterializeRiskAssessmentControlsHandler,
        Depends(get_materialize_risk_controls_handler),
    ],
) -> MaterializeControlsResponse:
    assert tenant_context.actor_user_id is not None
    controls = handler.handle(
        MaterializeRiskAssessmentControlsCommand(
            organization_id=tenant_context.organization_id,
            actor_id=tenant_context.actor_user_id,
            risk_assessment_id=RiskAssessmentId(value=assessment_id),
            control_ids=(
                None if request_body.control_ids is None else tuple(request_body.control_ids)
            ),
            allow_under_review=request_body.allow_under_review,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return MaterializeControlsResponse(
        items=[to_risk_control_response(item) for item in controls]
    )

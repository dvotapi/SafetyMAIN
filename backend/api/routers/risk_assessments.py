from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_approve_risk_assessment_handler,
    get_archive_risk_assessment_handler,
    get_create_risk_assessment_handler,
    get_get_risk_assessment_handler,
    get_list_risk_assessments_handler,
    get_risk_assessment_id,
    get_update_risk_assessment_handler,
    require_permission,
)
from backend.api.mappers.risk_assessments import (
    parse_acceptance,
    parse_competencies,
    parse_controls,
    parse_evaluation,
    parse_review_schedule,
    to_risk_assessment_list_response,
    to_risk_assessment_response,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    created_response,
    success_response,
)
from backend.api.operation_ids import (
    APPROVE_RISK_ASSESSMENT,
    ARCHIVE_RISK_ASSESSMENT,
    CREATE_RISK_ASSESSMENT,
    GET_RISK_ASSESSMENT,
    LIST_RISK_ASSESSMENTS,
    UPDATE_RISK_ASSESSMENT,
)
from backend.api.schemas.risk_assessments import (
    ApproveRiskAssessmentRequest,
    ArchiveRiskAssessmentRequest,
    CreateRiskAssessmentRequest,
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    UpdateRiskAssessmentRequest,
)
from backend.api.security import TenantContext
from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.authorization.policies.resource_permissions import (
    RISK_APPROVE,
    RISK_ARCHIVE,
    RISK_CREATE,
    RISK_READ,
    RISK_UPDATE,
)
from backend.core.application.commands.risk_assessment_lifecycle import (
    ApproveRiskAssessmentCommand,
    ArchiveRiskAssessmentCommand,
    CreateRiskAssessmentCommand,
    UpdateRiskAssessmentCommand,
)
from backend.core.application.handlers.create_risk_assessment import (
    CreateRiskAssessmentHandler,
)
from backend.core.application.handlers.get_list_risk_assessments import (
    GetRiskAssessmentHandler,
    ListRiskAssessmentsHandler,
)
from backend.core.application.handlers.risk_assessment_lifecycle import (
    ApproveRiskAssessmentHandler,
    ArchiveRiskAssessmentHandler,
)
from backend.core.application.handlers.update_risk_assessment import (
    UpdateRiskAssessmentHandler,
)
from backend.core.application.queries.risk_assessments import (
    GetRiskAssessmentQuery,
    ListRiskAssessmentsQuery,
)
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId

router = APIRouter(prefix="/risk-assessments", tags=["Risk Assessments"])


@router.post(
    "",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_RISK_ASSESSMENT,
    summary="Create a risk assessment",
    responses={
        **created_response(
            model=RiskAssessmentResponse,
            description="Risk assessment created.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_risk_assessment(
    request_body: CreateRiskAssessmentRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_CREATE))],
    handler: Annotated[
        CreateRiskAssessmentHandler, Depends(get_create_risk_assessment_handler)
    ],
) -> JSONResponse:
    assert tenant_context.actor_user_id is not None
    assessment = handler.handle(
        CreateRiskAssessmentCommand(
            organization_id=tenant_context.organization_id,
            actor_id=tenant_context.actor_user_id,
            hazard_id=HazardId(value=request_body.hazard_id),
            code=request_body.code,
            title=request_body.title,
            assessment_profile=AssessmentProfileCode(request_body.assessment_profile),
            assessed_object=AssessedObjectRef(
                object_type=AssessedObjectType(request_body.assessed_object.object_type),
                reference=request_body.assessed_object.reference,
            ),
            assessment_date=request_body.assessment_date,
            review_schedule=parse_review_schedule(request_body.review_schedule),
            competency_requirements=parse_competencies(
                request_body.competency_requirements
            )
            or (),
            extension_references=request_body.extension_references,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    body = to_risk_assessment_response(assessment)
    location = f"{API_V1_PREFIX}/risk-assessments/{assessment.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=RiskAssessmentListResponse,
    operation_id=LIST_RISK_ASSESSMENTS,
    summary="List risk assessments",
    responses={
        **success_response(
            model=RiskAssessmentListResponse,
            description="Risk assessments returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_risk_assessments(
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_READ))],
    handler: Annotated[
        ListRiskAssessmentsHandler, Depends(get_list_risk_assessments_handler)
    ],
    hazard_id: Annotated[UUID | None, Query()] = None,
    status_filter: Annotated[RiskAssessmentStatus | None, Query(alias="status")] = None,
    assessment_profile: Annotated[AssessmentProfileCode | None, Query()] = None,
    assessed_object_type: Annotated[str | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
    include_superseded: Annotated[bool, Query()] = True,
    search: Annotated[str | None, Query()] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> RiskAssessmentListResponse:
    page = handler.handle(
        ListRiskAssessmentsQuery(
            organization_id=tenant_context.organization_id,
            hazard_id=None if hazard_id is None else HazardId(value=hazard_id),
            status=status_filter,
            assessment_profile=assessment_profile,
            assessed_object_type=assessed_object_type,
            include_archived=include_archived,
            include_superseded=include_superseded,
            search=search,
            created_from=created_from,
            created_to=created_to,
            offset=offset,
            limit=limit,
        )
    )
    return to_risk_assessment_list_response(page)


@router.get(
    "/{risk_assessment_id}",
    response_model=RiskAssessmentResponse,
    operation_id=GET_RISK_ASSESSMENT,
    summary="Get a risk assessment",
    responses={
        **success_response(
            model=RiskAssessmentResponse,
            description="Risk assessment returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_risk_assessment(
    risk_assessment_id: Annotated[RiskAssessmentId, Depends(get_risk_assessment_id)],
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_READ))],
    handler: Annotated[
        GetRiskAssessmentHandler, Depends(get_get_risk_assessment_handler)
    ],
) -> RiskAssessmentResponse:
    assessment = handler.handle(
        GetRiskAssessmentQuery(
            organization_id=tenant_context.organization_id,
            risk_assessment_id=risk_assessment_id,
        )
    )
    return to_risk_assessment_response(assessment)


@router.patch(
    "/{risk_assessment_id}",
    response_model=RiskAssessmentResponse,
    operation_id=UPDATE_RISK_ASSESSMENT,
    summary="Update a risk assessment",
    responses={
        **success_response(
            model=RiskAssessmentResponse,
            description="Risk assessment updated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_risk_assessment(
    risk_assessment_id: Annotated[RiskAssessmentId, Depends(get_risk_assessment_id)],
    request_body: UpdateRiskAssessmentRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_UPDATE))],
    handler: Annotated[
        UpdateRiskAssessmentHandler, Depends(get_update_risk_assessment_handler)
    ],
    get_handler: Annotated[
        GetRiskAssessmentHandler, Depends(get_get_risk_assessment_handler)
    ],
) -> RiskAssessmentResponse:
    assert tenant_context.actor_user_id is not None
    current = get_handler.handle(
        GetRiskAssessmentQuery(
            organization_id=tenant_context.organization_id,
            risk_assessment_id=risk_assessment_id,
        )
    )
    assessed_object = None
    if request_body.assessed_object is not None:
        assessed_object = AssessedObjectRef(
            object_type=AssessedObjectType(
                request_body.assessed_object.object_type
            ),
            reference=request_body.assessed_object.reference,
        )
    assessment = handler.handle(
        UpdateRiskAssessmentCommand(
            organization_id=tenant_context.organization_id,
            risk_assessment_id=risk_assessment_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            title=request_body.title,
            assessed_object=assessed_object,
            assessment_date=request_body.assessment_date,
            review_schedule=parse_review_schedule(request_body.review_schedule),
            competency_requirements=parse_competencies(
                request_body.competency_requirements
            ),
            extension_references=request_body.extension_references,
            controls=parse_controls(request_body.controls),
            inherent_risk=parse_evaluation(current, request_body.inherent_risk),
            residual_risk=parse_evaluation(current, request_body.residual_risk),
            acceptance=parse_acceptance(request_body.acceptance),
            submit_for_review=request_body.submit_for_review,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_risk_assessment_response(assessment)


@router.post(
    "/{risk_assessment_id}/approve",
    response_model=RiskAssessmentResponse,
    operation_id=APPROVE_RISK_ASSESSMENT,
    summary="Approve a risk assessment",
    responses={
        **success_response(
            model=RiskAssessmentResponse,
            description="Risk assessment approved.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def approve_risk_assessment(
    risk_assessment_id: Annotated[RiskAssessmentId, Depends(get_risk_assessment_id)],
    request_body: ApproveRiskAssessmentRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_APPROVE))],
    handler: Annotated[
        ApproveRiskAssessmentHandler, Depends(get_approve_risk_assessment_handler)
    ],
) -> RiskAssessmentResponse:
    assert tenant_context.actor_user_id is not None
    assessment = handler.handle(
        ApproveRiskAssessmentCommand(
            organization_id=tenant_context.organization_id,
            risk_assessment_id=risk_assessment_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            acceptance=parse_acceptance(request_body.acceptance),
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_risk_assessment_response(assessment)


@router.post(
    "/{risk_assessment_id}/archive",
    response_model=RiskAssessmentResponse,
    operation_id=ARCHIVE_RISK_ASSESSMENT,
    summary="Archive a risk assessment",
    responses={
        **success_response(
            model=RiskAssessmentResponse,
            description="Risk assessment archived.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def archive_risk_assessment(
    risk_assessment_id: Annotated[RiskAssessmentId, Depends(get_risk_assessment_id)],
    request_body: ArchiveRiskAssessmentRequest,
    tenant_context: Annotated[TenantContext, Depends(require_permission(RISK_ARCHIVE))],
    handler: Annotated[
        ArchiveRiskAssessmentHandler, Depends(get_archive_risk_assessment_handler)
    ],
) -> RiskAssessmentResponse:
    assert tenant_context.actor_user_id is not None
    assessment = handler.handle(
        ArchiveRiskAssessmentCommand(
            organization_id=tenant_context.organization_id,
            risk_assessment_id=risk_assessment_id,
            actor_id=tenant_context.actor_user_id,
            expected_version=request_body.expected_version,
            reason=request_body.reason,
            audit_context=AuditContext.from_tenant(tenant_context),
        )
    )
    return to_risk_assessment_response(assessment)

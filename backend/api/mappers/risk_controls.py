from __future__ import annotations

from datetime import datetime

from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.api.schemas.risk_controls import (
    CreateRiskControlRequest,
    ImplementationPlanRequest,
    OwnerRequest,
    ReviewScheduleRequest,
    RiskControlListResponse,
    RiskControlResponse,
    ScopeReferenceRequest,
    SourceRequest,
    VerificationRequest,
)
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.risk_control_components import (
    ControlEffectivenessVerification,
    ControlOwner,
    ControlReviewSchedule,
    ControlSource,
    EvidenceReference,
    ImplementationMilestone,
    ImplementationPlan,
    ScopeReference,
    owner_to_dict,
    review_schedule_to_dict,
    source_to_dict,
)
from backend.core.domain.value_objects.risk_control_query import RiskControlPage
from backend.core.domain.value_objects.safety_enums import (
    ControlOwnerType,
    ControlScopeType,
    EffectivenessResult,
    EvidenceType,
    MilestoneStatus,
    ReviewBasis,
    RiskControlSourceType,
    VerificationType,
)
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId


def parse_scope(items: list[ScopeReferenceRequest]) -> tuple[ScopeReference, ...]:
    return tuple(
        ScopeReference(
            scope_type=ControlScopeType(item.scope_type),
            reference=item.reference,
        )
        for item in items
    )


def parse_owner(owner: OwnerRequest, *, actor_id: UserId, at: datetime) -> ControlOwner:
    return ControlOwner(
        owner_type=ControlOwnerType(owner.owner_type),
        owner_reference=owner.owner_reference,
        display_name_snapshot=owner.display_name_snapshot,
        assigned_at=at,
        assigned_by=actor_id,
    )


def parse_source(source: SourceRequest) -> ControlSource:
    return ControlSource(
        source_type=RiskControlSourceType(source.source_type),
        source_reference=source.source_reference,
        risk_assessment_id=(
            None
            if source.risk_assessment_id is None
            else RiskAssessmentId(value=source.risk_assessment_id)
        ),
        source_control_reference=source.source_control_reference,
    )


def parse_implementation(plan: ImplementationPlanRequest) -> ImplementationPlan:
    parsed: list[ImplementationMilestone] = []
    for item in plan.milestones:
        parsed.append(
            ImplementationMilestone(
                title=str(item["title"]),
                description=str(item.get("description", "")),
                due_date=item.get("due_date"),
                status=MilestoneStatus(str(item.get("status", "pending"))),
                completed_at=item.get("completed_at"),
                evidence_refs=tuple(item.get("evidence_refs", ())),
            )
        )
    return ImplementationPlan(
        target_start_date=plan.target_start_date,
        target_completion_date=plan.target_completion_date,
        implementation_method=plan.implementation_method,
        milestones=tuple(parsed),
        dependencies=tuple(plan.dependencies),
        resource_notes=plan.resource_notes,
        evidence_requirements=tuple(plan.evidence_requirements),
        progress=plan.progress,
        summary=plan.summary,
        evidence_waiver_reason=plan.evidence_waiver_reason,
    )


def parse_review_schedule(schedule: ReviewScheduleRequest) -> ControlReviewSchedule:
    return ControlReviewSchedule(
        review_required=schedule.review_required,
        review_frequency_days=schedule.review_frequency_days,
        next_review_date=schedule.next_review_date,
        review_basis=ReviewBasis(schedule.review_basis),
        escalation_policy_ref=schedule.escalation_policy_ref,
        no_review_reason=schedule.no_review_reason,
    )


def parse_verification(
    request: VerificationRequest,
    *,
    actor_id: UserId,
    at: datetime,
) -> ControlEffectivenessVerification:
    return ControlEffectivenessVerification(
        verification_type=VerificationType(request.verification_type),
        method=request.method,
        criteria=request.criteria,
        performed_at=at,
        performed_by=actor_id,
        result=EffectivenessResult(request.result),
        rating=request.rating,
        findings=request.findings,
        evidence_refs=tuple(request.evidence_refs),
        next_action=request.next_action,
        next_review_date=request.next_review_date,
        profile_key=request.profile_key,
        profile_version=request.profile_version,
    )


def parse_evidence(
    *,
    evidence_type: str,
    external_reference: str,
    title: str,
    description: str,
    actor_id: UserId,
    at: datetime,
    checksum: str | None,
    metadata: dict[str, str],
) -> EvidenceReference:
    return EvidenceReference(
        evidence_type=EvidenceType(evidence_type),
        external_reference=external_reference,
        title=title,
        description=description,
        captured_at=at,
        captured_by=actor_id,
        checksum=checksum,
        metadata=metadata,
    )


def to_risk_control_response(control: RiskControl) -> RiskControlResponse:
    latest = control.latest_effectiveness_result
    return RiskControlResponse(
        id=control.id.value,
        organization_id=control.organization_id.value,
        code=control.code.value,
        title=control.title,
        description=control.description,
        hierarchy_level=control.hierarchy_level.value,
        control_nature=control.control_nature.value,
        source=source_to_dict(control.source),
        hazard_id=None if control.hazard_id is None else control.hazard_id.value,
        risk_assessment_id=(
            None
            if control.risk_assessment_id is None
            else control.risk_assessment_id.value
        ),
        scope=[item.model_dump(mode="json") for item in control.scope],
        owner=owner_to_dict(control.owner),
        implementation=control.implementation.model_dump(mode="json"),
        evidence=[item.model_dump(mode="json") for item in control.evidence],
        verifications=[item.model_dump(mode="json") for item in control.verifications],
        review_schedule=review_schedule_to_dict(control.review_schedule),
        competency_requirements=[
            item.model_dump(mode="json") for item in control.competency_requirements
        ],
        related_entities=[
            item.model_dump(mode="json") for item in control.related_entities
        ],
        extension_data=dict(control.extension_data),
        lifecycle_status=control.lifecycle_status.value,  # type: ignore[arg-type]
        latest_effectiveness_result=None if latest is None else latest.value,
        next_review_date=control.next_review_date,
        verification_method_requirement=control.verification_method_requirement,
        version=control.version,
        created_at=control.created_at,
        updated_at=control.updated_at,
    )


def to_risk_control_list_response(page: RiskControlPage) -> RiskControlListResponse:
    return RiskControlListResponse(
        items=[to_risk_control_response(item) for item in page.items],
        pagination=PaginationResponse(
            total=page.total,
            offset=page.offset,
            limit=page.limit,
        ),
    )


def create_request_defaults(_request: CreateRiskControlRequest) -> None:
    return None

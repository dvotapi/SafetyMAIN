from __future__ import annotations

from uuid import uuid4

from backend.api.schemas.knowledge_objects import PaginationResponse
from backend.api.schemas.risk_assessments import (
    ControlMeasureRequest,
    ReviewScheduleRequest,
    RiskAcceptanceRequest,
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    RiskEvaluationRequest,
)
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.risk_assessment_components import (
    ControlMeasure,
    ReviewSchedule,
    RiskAcceptance,
    RiskEvaluation,
    RiskFactorScore,
    control_to_dict,
    evaluation_to_dict,
)
from backend.core.domain.value_objects.risk_assessment_query import RiskAssessmentPage
from backend.core.domain.value_objects.safety_enums import (
    CompetencyReferenceCode,
    ControlType,
    Probability,
    ReviewTrigger,
    RiskAcceptanceDecision,
    RiskFactorCode,
    RiskLevel,
    Severity,
)
from backend.core.domain.value_objects.safety_ids import ControlId


def to_risk_assessment_response(assessment: RiskAssessment) -> RiskAssessmentResponse:
    return RiskAssessmentResponse(
        id=assessment.id.value,
        organization_id=assessment.organization_id.value,
        hazard_id=assessment.hazard_id.value,
        code=assessment.code.value,
        title=assessment.title,
        assessment_profile=assessment.assessment_profile.value,
        assessed_object={
            "object_type": assessment.assessed_object.object_type.value,
            "reference": assessment.assessed_object.reference,
        },
        assessor_id=assessment.assessor_id.value,
        assessment_date=assessment.assessment_date,
        review_schedule={
            "review_due_date": assessment.review_schedule.review_due_date,
            "review_frequency_days": assessment.review_schedule.review_frequency_days,
            "review_reason": assessment.review_schedule.review_reason,
            "triggered_by": (
                None
                if assessment.review_schedule.triggered_by is None
                else assessment.review_schedule.triggered_by.value
            ),
        },
        inherent_risk=evaluation_to_dict(assessment.inherent_risk),
        residual_risk=evaluation_to_dict(assessment.residual_risk),
        controls=[control_to_dict(control) for control in assessment.controls],
        acceptance=(
            None
            if assessment.acceptance is None
            else {
                "decision": assessment.acceptance.decision.value,
                "reviewer_id": (
                    None
                    if assessment.acceptance.reviewer_id is None
                    else str(assessment.acceptance.reviewer_id.value)
                ),
                "justification": assessment.acceptance.justification,
                "approved_at": assessment.acceptance.approved_at,
            }
        ),
        competency_requirements=[
            item.value for item in assessment.competency_requirements
        ],
        extension_references=dict(assessment.extension_references),
        status=assessment.status.value,  # type: ignore[arg-type]
        superseded_by_id=(
            None
            if assessment.superseded_by_id is None
            else assessment.superseded_by_id.value
        ),
        archived_at=assessment.archived_at,
        archived_by=(
            None if assessment.archived_by is None else assessment.archived_by.value
        ),
        approved_at=assessment.approved_at,
        approved_by=(
            None if assessment.approved_by is None else assessment.approved_by.value
        ),
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        version=assessment.version,
    )


def to_risk_assessment_list_response(
    page: RiskAssessmentPage,
) -> RiskAssessmentListResponse:
    return RiskAssessmentListResponse(
        items=[to_risk_assessment_response(item) for item in page.items],
        pagination=PaginationResponse(
            total=page.total,
            offset=page.offset,
            limit=page.limit,
        ),
    )


def parse_review_schedule(
    payload: ReviewScheduleRequest | None,
) -> ReviewSchedule | None:
    if payload is None:
        return None
    return ReviewSchedule(
        review_due_date=payload.review_due_date,
        review_frequency_days=payload.review_frequency_days,
        review_reason=payload.review_reason,
        triggered_by=(
            None
            if payload.triggered_by is None
            else ReviewTrigger(payload.triggered_by)
        ),
    )


def parse_controls(
    payloads: list[ControlMeasureRequest] | None,
) -> tuple[ControlMeasure, ...] | None:
    if payloads is None:
        return None
    return tuple(
        ControlMeasure(
            id=ControlId(value=item.id or uuid4()),
            control_type=ControlType(item.control_type),
            description=item.description,
            responsible=item.responsible,
            implemented=item.implemented,
            effective=item.effective,
        )
        for item in payloads
    )


def parse_acceptance(
    payload: RiskAcceptanceRequest | None,
) -> RiskAcceptance | None:
    if payload is None:
        return None
    return RiskAcceptance(
        decision=RiskAcceptanceDecision(payload.decision),
        justification=payload.justification,
        reviewer_id=(
            None
            if payload.reviewer_id is None
            else UserId(value=payload.reviewer_id)
        ),
    )


def parse_evaluation(
    assessment: RiskAssessment,
    payload: RiskEvaluationRequest | None,
) -> RiskEvaluation | None:
    if payload is None:
        return None
    if payload.probability is not None and payload.severity is not None:
        extra = tuple(
            RiskFactorScore(
                factor=RiskFactorCode(item.factor),
                score=item.score,
            )
            for item in payload.factors
            if item.factor
            not in {
                RiskFactorCode.PROBABILITY.value,
                RiskFactorCode.SEVERITY.value,
            }
        )
        return assessment.build_evaluation(
            probability=(
                payload.probability
                if isinstance(payload.probability, int)
                else Probability(payload.probability)
            ),
            severity=(
                payload.severity
                if isinstance(payload.severity, int)
                else Severity(payload.severity)
            ),
            extra_factors=extra,
            level=None if payload.level is None else RiskLevel(payload.level),
            explanation=payload.explanation,
        )
    if payload.factors:
        return RiskEvaluation(
            factors=tuple(
                RiskFactorScore(
                    factor=RiskFactorCode(item.factor),
                    score=item.score,
                )
                for item in payload.factors
            ),
            level=RiskLevel(payload.level or "medium"),
            explanation=payload.explanation,
        )
    raise ValueError("Risk evaluation requires probability and severity or factors.")


def parse_competencies(values: list[str] | None) -> tuple[CompetencyReferenceCode, ...] | None:
    if values is None:
        return None
    return tuple(CompetencyReferenceCode(value) for value in values)

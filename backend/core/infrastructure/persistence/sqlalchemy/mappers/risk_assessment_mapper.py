from __future__ import annotations

from datetime import datetime
from uuid import UUID

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    RiskAcceptance,
    ReviewSchedule,
    control_from_dict,
    control_to_dict,
    evaluation_from_dict,
    evaluation_to_dict,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    CompetencyReferenceCode,
    ReviewTrigger,
    RiskAcceptanceDecision,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId
from backend.core.infrastructure.persistence.sqlalchemy.models.risk_assessment_model import (
    RiskAssessmentModel,
)


def _review_schedule_to_dict(schedule: ReviewSchedule) -> dict[str, object]:
    return {
        "review_due_date": (
            None
            if schedule.review_due_date is None
            else schedule.review_due_date.isoformat()
        ),
        "review_frequency_days": schedule.review_frequency_days,
        "review_reason": schedule.review_reason,
        "triggered_by": (
            None if schedule.triggered_by is None else schedule.triggered_by.value
        ),
    }


def _review_schedule_from_dict(payload: dict[str, object] | None) -> ReviewSchedule:
    data = payload or {}
    due = data.get("review_due_date")
    triggered = data.get("triggered_by")
    return ReviewSchedule(
        review_due_date=None if due is None else datetime.fromisoformat(str(due)),
        review_frequency_days=(
            None
            if data.get("review_frequency_days") is None
            else int(data["review_frequency_days"])  # type: ignore[arg-type]
        ),
        review_reason=(
            None if data.get("review_reason") is None else str(data["review_reason"])
        ),
        triggered_by=(
            None if triggered is None else ReviewTrigger(str(triggered))
        ),
    )


def _acceptance_to_dict(acceptance: RiskAcceptance | None) -> dict[str, object] | None:
    if acceptance is None:
        return None
    return {
        "decision": acceptance.decision.value,
        "reviewer_id": (
            None if acceptance.reviewer_id is None else str(acceptance.reviewer_id.value)
        ),
        "justification": acceptance.justification,
        "approved_at": (
            None
            if acceptance.approved_at is None
            else acceptance.approved_at.isoformat()
        ),
    }


def _acceptance_from_dict(payload: dict[str, object] | None) -> RiskAcceptance | None:
    if payload is None:
        return None
    reviewer = payload.get("reviewer_id")
    approved_at = payload.get("approved_at")
    return RiskAcceptance(
        decision=RiskAcceptanceDecision(str(payload["decision"])),
        reviewer_id=None if reviewer is None else UserId(value=UUID(str(reviewer))),
        justification=str(payload.get("justification", "")),
        approved_at=(
            None if approved_at is None else datetime.fromisoformat(str(approved_at))
        ),
    )


def to_model(assessment: RiskAssessment) -> RiskAssessmentModel:
    return RiskAssessmentModel(
        id=assessment.id.value,
        organization_id=assessment.organization_id.value,
        hazard_id=assessment.hazard_id.value,
        code=assessment.code.value,
        title=assessment.title,
        assessment_profile=assessment.assessment_profile.value,
        assessed_object_type=assessment.assessed_object.object_type.value,
        assessed_object_reference=assessment.assessed_object.reference,
        assessor_id=assessment.assessor_id.value,
        assessment_date=assessment.assessment_date,
        review_schedule=_review_schedule_to_dict(assessment.review_schedule),
        inherent_risk=evaluation_to_dict(assessment.inherent_risk),
        residual_risk=evaluation_to_dict(assessment.residual_risk),
        controls=[control_to_dict(control) for control in assessment.controls],
        acceptance=_acceptance_to_dict(assessment.acceptance),
        competency_requirements=[
            item.value for item in assessment.competency_requirements
        ],
        extension_references=dict(assessment.extension_references),
        status=assessment.status.value,
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


def apply_to_model(model: RiskAssessmentModel, assessment: RiskAssessment) -> None:
    mapped = to_model(assessment)
    for column in RiskAssessmentModel.__table__.columns:
        if column.name == "id":
            continue
        setattr(model, column.name, getattr(mapped, column.name))


def to_domain(model: RiskAssessmentModel) -> RiskAssessment:
    return RiskAssessment(
        id=RiskAssessmentId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        hazard_id=HazardId(value=model.hazard_id),
        code=RiskAssessmentCode(value=model.code),
        title=model.title,
        assessment_profile=AssessmentProfileCode(model.assessment_profile),
        assessed_object=AssessedObjectRef(
            object_type=AssessedObjectType(model.assessed_object_type),
            reference=model.assessed_object_reference,
        ),
        assessor_id=UserId(value=model.assessor_id),
        assessment_date=model.assessment_date,
        review_schedule=_review_schedule_from_dict(model.review_schedule),
        inherent_risk=evaluation_from_dict(model.inherent_risk),
        residual_risk=evaluation_from_dict(model.residual_risk),
        controls=tuple(control_from_dict(item) for item in (model.controls or [])),
        acceptance=_acceptance_from_dict(model.acceptance),
        competency_requirements=tuple(
            CompetencyReferenceCode(item)
            for item in (model.competency_requirements or [])
        ),
        extension_references=dict(model.extension_references or {}),
        status=RiskAssessmentStatus(model.status),
        superseded_by_id=(
            None
            if model.superseded_by_id is None
            else RiskAssessmentId(value=model.superseded_by_id)
        ),
        archived_at=model.archived_at,
        archived_by=(
            None if model.archived_by is None else UserId(value=model.archived_by)
        ),
        approved_at=model.approved_at,
        approved_by=(
            None if model.approved_by is None else UserId(value=model.approved_by)
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
        version=model.version,
    )

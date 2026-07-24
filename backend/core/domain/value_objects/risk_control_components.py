from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.safety_enums import (
    ControlCompetencyRequirementType,
    ControlOwnerType,
    ControlRelatedEntityType,
    ControlScopeType,
    EffectivenessResult,
    EvidenceType,
    MilestoneStatus,
    ReviewBasis,
    RiskControlSourceType,
    VerificationType,
)
from backend.core.domain.value_objects.safety_ids import RiskAssessmentId


class ScopeReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    scope_type: ControlScopeType
    reference: str

    @field_validator("reference")
    @classmethod
    def normalize(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Scope reference must not be empty.")
        return normalized


class ControlOwner(BaseModel):
    model_config = ConfigDict(frozen=True)

    owner_type: ControlOwnerType
    owner_reference: str
    display_name_snapshot: str
    assigned_at: datetime
    assigned_by: UserId

    @field_validator("owner_reference", "display_name_snapshot")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Owner fields must not be empty.")
        return normalized


class OwnerAssignmentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    owner: ControlOwner
    changed_at: datetime
    changed_by: UserId
    reason: str = ""


class ControlSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: RiskControlSourceType
    source_reference: str | None = None
    risk_assessment_id: RiskAssessmentId | None = None
    source_control_reference: str | None = None
    assessment_version: int | None = None
    assessment_approved_at: datetime | None = None
    residual_level: str | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)


class ImplementationMilestone(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = ""
    due_date: datetime | None = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    completed_at: datetime | None = None
    evidence_refs: tuple[str, ...] = ()

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Milestone title is required.")
        return normalized


class EvidenceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    external_reference: str
    title: str
    description: str = ""
    captured_at: datetime
    captured_by: UserId
    checksum: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("external_reference", "title")
    @classmethod
    def require_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Evidence reference and title are required.")
        return normalized


class ImplementationPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_start_date: datetime | None = None
    target_completion_date: datetime | None = None
    actual_start_date: datetime | None = None
    actual_completion_date: datetime | None = None
    implementation_method: str = ""
    milestones: tuple[ImplementationMilestone, ...] = ()
    dependencies: tuple[str, ...] = ()
    resource_notes: str = ""
    evidence_requirements: tuple[str, ...] = ()
    progress: int = Field(default=0, ge=0, le=100)
    summary: str = ""
    evidence_waiver_reason: str | None = None

    def validate_dates(self) -> None:
        if (
            self.target_start_date is not None
            and self.target_completion_date is not None
            and self.target_completion_date < self.target_start_date
        ):
            raise ValueError("Target completion cannot be earlier than target start.")
        if (
            self.actual_start_date is not None
            and self.actual_completion_date is not None
            and self.actual_completion_date < self.actual_start_date
        ):
            raise ValueError("Actual completion cannot be earlier than actual start.")


class ControlEffectivenessVerification(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    verification_type: VerificationType
    method: str
    criteria: str = ""
    performed_at: datetime
    performed_by: UserId
    result: EffectivenessResult
    rating: str | None = None
    findings: str = ""
    evidence_refs: tuple[str, ...] = ()
    related_inspection_id: str | None = None
    related_incident_id: str | None = None
    next_action: str | None = None
    next_review_date: datetime | None = None
    profile_key: str = "default"
    profile_version: str = "1"

    @field_validator("method")
    @classmethod
    def require_method(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Verification method is required.")
        return normalized


class ControlReviewSchedule(BaseModel):
    model_config = ConfigDict(frozen=True)

    review_required: bool = True
    review_frequency_days: int | None = Field(default=365, ge=1)
    next_review_date: datetime | None = None
    last_review_date: datetime | None = None
    review_basis: ReviewBasis = ReviewBasis.FIXED_INTERVAL
    escalation_policy_ref: str | None = None
    no_review_reason: str | None = None


class ControlCompetencyRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    competency_ref: str
    requirement_type: ControlCompetencyRequirementType
    required_level: str | None = None
    training_program_ref: str | None = None
    notes: str = ""

    @field_validator("competency_ref")
    @classmethod
    def require_ref(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Competency reference is required.")
        return normalized


class RelatedEntityReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    entity_type: ControlRelatedEntityType
    reference: str

    @field_validator("reference")
    @classmethod
    def require_ref(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Related entity reference is required.")
        return normalized


class SuspensionInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: str
    suspended_by: UserId
    suspended_at: datetime
    expected_resolution_date: datetime | None = None

    @field_validator("reason")
    @classmethod
    def require_reason(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Suspension reason is required.")
        return normalized


def owner_to_dict(owner: ControlOwner | None) -> dict[str, Any] | None:
    if owner is None:
        return None
    return {
        "owner_type": owner.owner_type.value,
        "owner_reference": owner.owner_reference,
        "display_name_snapshot": owner.display_name_snapshot,
        "assigned_at": owner.assigned_at.isoformat(),
        "assigned_by": str(owner.assigned_by.value),
    }


def owner_from_dict(payload: dict[str, Any] | None) -> ControlOwner | None:
    if payload is None:
        return None
    return ControlOwner(
        owner_type=ControlOwnerType(payload["owner_type"]),
        owner_reference=payload["owner_reference"],
        display_name_snapshot=payload["display_name_snapshot"],
        assigned_at=datetime.fromisoformat(payload["assigned_at"]),
        assigned_by=UserId(value=UUID(payload["assigned_by"])),
    )


def _jsonable(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def source_to_dict(source: ControlSource) -> dict[str, Any]:
    return _jsonable(source)


def source_from_dict(payload: dict[str, Any]) -> ControlSource:
    return ControlSource.model_validate(payload)


def scope_to_list(scope: tuple[ScopeReference, ...]) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in scope]


def scope_from_list(payload: list[dict[str, Any]] | None) -> tuple[ScopeReference, ...]:
    return tuple(ScopeReference.model_validate(item) for item in (payload or []))


def owner_history_to_list(
    history: tuple[OwnerAssignmentRecord, ...],
) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in history]


def owner_history_from_list(
    payload: list[dict[str, Any]] | None,
) -> tuple[OwnerAssignmentRecord, ...]:
    return tuple(OwnerAssignmentRecord.model_validate(item) for item in (payload or []))


def implementation_to_dict(plan: ImplementationPlan) -> dict[str, Any]:
    return _jsonable(plan)


def implementation_from_dict(payload: dict[str, Any] | None) -> ImplementationPlan:
    return ImplementationPlan.model_validate(payload or {})


def evidence_to_list(items: tuple[EvidenceReference, ...]) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in items]


def evidence_from_list(
    payload: list[dict[str, Any]] | None,
) -> tuple[EvidenceReference, ...]:
    return tuple(EvidenceReference.model_validate(item) for item in (payload or []))


def verifications_to_list(
    items: tuple[ControlEffectivenessVerification, ...],
) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in items]


def verifications_from_list(
    payload: list[dict[str, Any]] | None,
) -> tuple[ControlEffectivenessVerification, ...]:
    return tuple(
        ControlEffectivenessVerification.model_validate(item) for item in (payload or [])
    )


def review_schedule_to_dict(schedule: ControlReviewSchedule) -> dict[str, Any]:
    return _jsonable(schedule)


def review_schedule_from_dict(
    payload: dict[str, Any] | None,
) -> ControlReviewSchedule:
    return ControlReviewSchedule.model_validate(payload or {})


def competencies_to_list(
    items: tuple[ControlCompetencyRequirement, ...],
) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in items]


def competencies_from_list(
    payload: list[dict[str, Any]] | None,
) -> tuple[ControlCompetencyRequirement, ...]:
    return tuple(
        ControlCompetencyRequirement.model_validate(item) for item in (payload or [])
    )


def related_to_list(
    items: tuple[RelatedEntityReference, ...],
) -> list[dict[str, Any]]:
    return [_jsonable(item) for item in items]


def related_from_list(
    payload: list[dict[str, Any]] | None,
) -> tuple[RelatedEntityReference, ...]:
    return tuple(RelatedEntityReference.model_validate(item) for item in (payload or []))


def suspension_to_dict(info: SuspensionInfo | None) -> dict[str, Any] | None:
    if info is None:
        return None
    return _jsonable(info)


def suspension_from_dict(payload: dict[str, Any] | None) -> SuspensionInfo | None:
    if payload is None:
        return None
    return SuspensionInfo.model_validate(payload)

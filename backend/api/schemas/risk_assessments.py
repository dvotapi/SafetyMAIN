from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse

RiskAssessmentStatusValue = Literal[
    "draft",
    "under_review",
    "approved",
    "superseded",
    "archived",
]
AssessmentProfileValue = Literal[
    "simple_3x3",
    "simple_5x5",
    "corporate_custom",
    "russian_occupational_risk",
    "industrial_safety",
    "fire_safety",
    "environmental_risk",
    "transport_risk",
    "adr_risk",
]
AssessedObjectTypeValue = Literal[
    "workplace",
    "job_position",
    "work_activity",
    "equipment",
    "vehicle",
    "production_process",
    "location",
    "contractor_activity",
    "chemical",
    "emergency_scenario",
]
RiskLevelValue = Literal["low", "medium", "high", "extreme"]
ProbabilityValue = Literal[
    "rare",
    "unlikely",
    "possible",
    "likely",
    "almost_certain",
]
SeverityValue = Literal[
    "insignificant",
    "minor",
    "moderate",
    "major",
    "catastrophic",
]
ControlTypeValue = Literal[
    "elimination",
    "substitution",
    "engineering",
    "administrative",
    "ppe",
]
AcceptanceDecisionValue = Literal[
    "accepted",
    "conditionally_accepted",
    "not_accepted",
    "requires_escalation",
]


class AssessedObjectRequest(BaseModel):
    object_type: AssessedObjectTypeValue
    reference: str = Field(min_length=1, max_length=256)


class RiskFactorScoreRequest(BaseModel):
    factor: str
    score: int = Field(ge=1, le=5)


class RiskEvaluationRequest(BaseModel):
    probability: ProbabilityValue | int | None = None
    severity: SeverityValue | int | None = None
    factors: list[RiskFactorScoreRequest] = Field(default_factory=list)
    level: RiskLevelValue | None = None
    explanation: str = ""


class ControlMeasureRequest(BaseModel):
    id: UUID | None = None
    control_type: ControlTypeValue
    description: str = Field(min_length=1)
    responsible: str | None = None
    implemented: bool = False
    effective: bool | None = None


class RiskAcceptanceRequest(BaseModel):
    decision: AcceptanceDecisionValue
    justification: str = ""
    reviewer_id: UUID | None = None


class ReviewScheduleRequest(BaseModel):
    review_due_date: datetime | None = None
    review_frequency_days: int | None = Field(default=None, ge=1)
    review_reason: str | None = None
    triggered_by: str | None = None


class CreateRiskAssessmentRequest(BaseModel):
    hazard_id: UUID
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    assessment_profile: AssessmentProfileValue
    assessed_object: AssessedObjectRequest
    assessment_date: datetime | None = None
    review_schedule: ReviewScheduleRequest | None = None
    competency_requirements: list[str] = Field(default_factory=list)
    extension_references: dict[str, str] = Field(default_factory=dict)


class UpdateRiskAssessmentRequest(BaseModel):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=512)
    assessed_object: AssessedObjectRequest | None = None
    assessment_date: datetime | None = None
    review_schedule: ReviewScheduleRequest | None = None
    competency_requirements: list[str] | None = None
    extension_references: dict[str, str] | None = None
    controls: list[ControlMeasureRequest] | None = None
    inherent_risk: RiskEvaluationRequest | None = None
    residual_risk: RiskEvaluationRequest | None = None
    acceptance: RiskAcceptanceRequest | None = None
    submit_for_review: bool = False


class ApproveRiskAssessmentRequest(BaseModel):
    expected_version: int = Field(ge=1)
    acceptance: RiskAcceptanceRequest | None = None


class ArchiveRiskAssessmentRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=2000)


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    hazard_id: UUID
    code: str
    title: str
    assessment_profile: str
    assessed_object: dict[str, Any]
    assessor_id: UUID
    assessment_date: datetime
    review_schedule: dict[str, Any]
    inherent_risk: dict[str, Any] | None = None
    residual_risk: dict[str, Any] | None = None
    controls: list[dict[str, Any]] = Field(default_factory=list)
    acceptance: dict[str, Any] | None = None
    competency_requirements: list[str] = Field(default_factory=list)
    extension_references: dict[str, str] = Field(default_factory=dict)
    status: RiskAssessmentStatusValue
    superseded_by_id: UUID | None = None
    archived_at: datetime | None = None
    archived_by: UUID | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    version: int


class RiskAssessmentListResponse(BaseModel):
    items: list[RiskAssessmentResponse]
    pagination: PaginationResponse

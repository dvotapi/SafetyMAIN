from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse

RiskControlStatusValue = Literal[
    "draft",
    "planned",
    "in_implementation",
    "implemented",
    "verified_effective",
    "verified_ineffective",
    "suspended",
    "superseded",
    "archived",
    "cancelled",
]
ControlTypeValue = Literal[
    "elimination",
    "substitution",
    "engineering",
    "administrative",
    "ppe",
]
ControlNatureValue = Literal["preventive", "detective", "mitigating", "recovery"]
SourceTypeValue = Literal[
    "risk_assessment",
    "regulatory_requirement",
    "corporate_standard",
    "incident",
    "inspection",
    "corrective_action",
    "management_decision",
    "other",
]
OwnerTypeValue = Literal[
    "user",
    "employee",
    "role",
    "organizational_unit",
    "external_party",
]
EffectivenessResultValue = Literal[
    "effective",
    "partially_effective",
    "ineffective",
    "not_verified",
    "not_applicable",
]


class ScopeReferenceRequest(BaseModel):
    scope_type: str
    reference: str = Field(min_length=1)


class OwnerRequest(BaseModel):
    owner_type: OwnerTypeValue
    owner_reference: str = Field(min_length=1)
    display_name_snapshot: str = Field(min_length=1)


class SourceRequest(BaseModel):
    source_type: SourceTypeValue
    source_reference: str | None = None
    risk_assessment_id: UUID | None = None
    source_control_reference: str | None = None


class ImplementationPlanRequest(BaseModel):
    target_start_date: datetime | None = None
    target_completion_date: datetime | None = None
    implementation_method: str = ""
    progress: int = Field(default=0, ge=0, le=100)
    summary: str = ""
    evidence_waiver_reason: str | None = None
    milestones: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    resource_notes: str = ""
    evidence_requirements: list[str] = Field(default_factory=list)


class ReviewScheduleRequest(BaseModel):
    review_required: bool = True
    review_frequency_days: int | None = Field(default=365, ge=1)
    next_review_date: datetime | None = None
    review_basis: str = "fixed_interval"
    no_review_reason: str | None = None
    escalation_policy_ref: str | None = None


class CreateRiskControlRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1)
    hierarchy_level: ControlTypeValue
    control_nature: ControlNatureValue
    source: SourceRequest
    scope: list[ScopeReferenceRequest] = Field(min_length=1)
    hazard_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    owner: OwnerRequest | None = None
    implementation: ImplementationPlanRequest | None = None
    review_schedule: ReviewScheduleRequest | None = None
    verification_method_requirement: str = ""
    extension_data: dict[str, Any] = Field(default_factory=dict)


class UpdateRiskControlRequest(BaseModel):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, min_length=1)
    hierarchy_level: ControlTypeValue | None = None
    control_nature: ControlNatureValue | None = None
    scope: list[ScopeReferenceRequest] | None = None
    verification_method_requirement: str | None = None
    implementation: ImplementationPlanRequest | None = None
    extension_data: dict[str, Any] | None = None


class AssignOwnerRequest(BaseModel):
    expected_version: int = Field(ge=1)
    owner: OwnerRequest
    reason: str = ""


class PlanRiskControlRequest(BaseModel):
    expected_version: int = Field(ge=1)
    implementation: ImplementationPlanRequest
    verification_method_requirement: str | None = None


class ProgressRequest(BaseModel):
    expected_version: int = Field(ge=1)
    progress: int = Field(ge=0, le=100)
    summary: str | None = None


class EvidenceRequest(BaseModel):
    expected_version: int = Field(ge=1)
    evidence_type: str
    external_reference: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    checksum: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    allow_after_implemented: bool = False


class CompleteImplementationRequest(BaseModel):
    expected_version: int = Field(ge=1)
    summary: str = Field(min_length=1)
    evidence_waiver_reason: str | None = None
    allow_incomplete_milestones: bool = False


class VerificationRequest(BaseModel):
    expected_version: int = Field(ge=1)
    verification_type: str = "initial"
    method: str = Field(min_length=1)
    criteria: str = ""
    result: EffectivenessResultValue
    rating: str | None = None
    findings: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    next_action: str | None = None
    next_review_date: datetime | None = None
    profile_key: str = "default"
    profile_version: str = "1"


class ScheduleReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)
    schedule: ReviewScheduleRequest


class CompleteReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)
    next_review_date: datetime | None = None
    verification: VerificationRequest | None = None


class ReasonVersionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1)


class SuspendRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1)
    expected_resolution_date: datetime | None = None


class VersionOnlyRequest(BaseModel):
    expected_version: int = Field(ge=1)


class SupersedeRequest(BaseModel):
    expected_version: int = Field(ge=1)
    replacement_control_id: UUID
    reason: str = Field(min_length=1)


class MaterializeControlsRequest(BaseModel):
    control_ids: list[UUID] | None = None
    allow_under_review: bool = False


class RiskControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    organization_id: UUID
    code: str
    title: str
    description: str
    hierarchy_level: str
    control_nature: str
    source: dict[str, Any]
    hazard_id: UUID | None
    risk_assessment_id: UUID | None
    scope: list[dict[str, Any]]
    owner: dict[str, Any] | None
    implementation: dict[str, Any]
    evidence: list[dict[str, Any]]
    verifications: list[dict[str, Any]]
    review_schedule: dict[str, Any]
    competency_requirements: list[dict[str, Any]]
    related_entities: list[dict[str, Any]]
    extension_data: dict[str, Any]
    lifecycle_status: RiskControlStatusValue
    latest_effectiveness_result: str | None
    next_review_date: datetime | None
    is_overdue: bool
    verification_method_requirement: str
    version: int
    created_at: datetime
    updated_at: datetime


class RiskControlListResponse(BaseModel):
    items: list[RiskControlResponse]
    pagination: PaginationResponse


class MaterializeControlsResponse(BaseModel):
    items: list[RiskControlResponse]

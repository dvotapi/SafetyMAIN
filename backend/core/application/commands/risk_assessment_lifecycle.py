from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    ControlMeasure,
    RiskAcceptance,
    RiskEvaluation,
    ReviewSchedule,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    CompetencyReferenceCode,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId


@dataclass(frozen=True, slots=True)
class CreateRiskAssessmentCommand:
    organization_id: OrganizationId
    actor_id: UserId
    hazard_id: HazardId
    code: RiskAssessmentCode | str
    title: str
    assessment_profile: AssessmentProfileCode
    assessed_object: AssessedObjectRef
    assessment_date: datetime | None = None
    review_schedule: ReviewSchedule | None = None
    competency_requirements: tuple[CompetencyReferenceCode, ...] = ()
    extension_references: dict[str, str] | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateRiskAssessmentCommand:
    organization_id: OrganizationId
    risk_assessment_id: RiskAssessmentId
    actor_id: UserId
    expected_version: int
    title: str | None = None
    assessed_object: AssessedObjectRef | None = None
    assessment_date: datetime | None = None
    review_schedule: ReviewSchedule | None = None
    competency_requirements: tuple[CompetencyReferenceCode, ...] | None = None
    extension_references: dict[str, str] | None = None
    controls: tuple[ControlMeasure, ...] | None = None
    inherent_risk: RiskEvaluation | None = None
    residual_risk: RiskEvaluation | None = None
    acceptance: RiskAcceptance | None = None
    submit_for_review: bool = False
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ApproveRiskAssessmentCommand:
    organization_id: OrganizationId
    risk_assessment_id: RiskAssessmentId
    actor_id: UserId
    expected_version: int
    acceptance: RiskAcceptance | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ArchiveRiskAssessmentCommand:
    organization_id: OrganizationId
    risk_assessment_id: RiskAssessmentId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class SupersedeRiskAssessmentCommand:
    organization_id: OrganizationId
    risk_assessment_id: RiskAssessmentId
    actor_id: UserId
    expected_version: int
    superseded_by_id: RiskAssessmentId
    audit_context: AuditContext | None = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_components import (
    ControlCompetencyRequirement,
    ControlEffectivenessVerification,
    ControlOwner,
    ControlReviewSchedule,
    ControlSource,
    EvidenceReference,
    ImplementationMilestone,
    ImplementationPlan,
    RelatedEntityReference,
    ScopeReference,
    SuspensionInfo,
)
from backend.core.domain.value_objects.safety_enums import ControlNature, ControlType
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)


@dataclass(frozen=True, slots=True)
class CreateRiskControlCommand:
    organization_id: OrganizationId
    actor_id: UserId
    code: RiskControlCode | str
    title: str
    description: str
    hierarchy_level: ControlType
    control_nature: ControlNature
    source: ControlSource
    scope: tuple[ScopeReference, ...]
    hazard_id: HazardId | None = None
    risk_assessment_id: RiskAssessmentId | None = None
    owner: ControlOwner | None = None
    implementation: ImplementationPlan | None = None
    review_schedule: ControlReviewSchedule | None = None
    competency_requirements: tuple[ControlCompetencyRequirement, ...] = ()
    related_entities: tuple[RelatedEntityReference, ...] = ()
    extension_data: dict[str, Any] | None = None
    verification_method_requirement: str = ""
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    title: str | None = None
    description: str | None = None
    hierarchy_level: ControlType | None = None
    control_nature: ControlNature | None = None
    scope: tuple[ScopeReference, ...] | None = None
    competency_requirements: tuple[ControlCompetencyRequirement, ...] | None = None
    related_entities: tuple[RelatedEntityReference, ...] | None = None
    extension_data: dict[str, Any] | None = None
    verification_method_requirement: str | None = None
    implementation: ImplementationPlan | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class AssignRiskControlOwnerCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    owner: ControlOwner
    reason: str = ""
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class PlanRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    implementation: ImplementationPlan
    verification_method_requirement: str | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class StartRiskControlImplementationCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class UpdateRiskControlProgressCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    progress: int
    summary: str | None = None
    milestones: tuple[ImplementationMilestone, ...] | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class AddRiskControlEvidenceCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    evidence: EvidenceReference
    allow_after_implemented: bool = False
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class CompleteRiskControlImplementationCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    summary: str
    evidence_waiver_reason: str | None = None
    allow_incomplete_milestones: bool = False
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RecordRiskControlVerificationCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    verification: ControlEffectivenessVerification
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ScheduleRiskControlReviewCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    schedule: ControlReviewSchedule
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class CompleteRiskControlReviewCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    verification: ControlEffectivenessVerification | None = None
    next_review_date: datetime | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class SuspendRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    suspension: SuspensionInfo
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ResumeRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class SupersedeRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    replacement_control_id: RiskControlId
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ArchiveRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class CancelRiskControlCommand:
    organization_id: OrganizationId
    control_id: RiskControlId
    actor_id: UserId
    expected_version: int
    reason: str
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class MaterializeRiskAssessmentControlsCommand:
    organization_id: OrganizationId
    actor_id: UserId
    risk_assessment_id: RiskAssessmentId
    control_ids: tuple[UUID, ...] | None = None
    allow_under_review: bool = False
    audit_context: AuditContext | None = None

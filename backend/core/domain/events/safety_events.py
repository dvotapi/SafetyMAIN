from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)


class SafetyDomainEvent(BaseModel):
    """Base in-process Safety domain event (no messaging infrastructure)."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    organization_id: OrganizationId
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    actor_id: UserId | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class HazardCreated(SafetyDomainEvent):
    event_type: str = "hazard.created"
    aggregate_type: str = "hazard"
    hazard_id: HazardId


class HazardUpdated(SafetyDomainEvent):
    event_type: str = "hazard.updated"
    aggregate_type: str = "hazard"
    hazard_id: HazardId


class HazardActivated(SafetyDomainEvent):
    event_type: str = "hazard.activated"
    aggregate_type: str = "hazard"
    hazard_id: HazardId
    previous_status: str
    new_status: str


class HazardArchived(SafetyDomainEvent):
    event_type: str = "hazard.archived"
    aggregate_type: str = "hazard"
    hazard_id: HazardId
    previous_status: str
    new_status: str
    reason: str


class HazardRestored(SafetyDomainEvent):
    event_type: str = "hazard.restored"
    aggregate_type: str = "hazard"
    hazard_id: HazardId
    previous_status: str
    new_status: str
    reason: str


class RiskAssessmentCreated(SafetyDomainEvent):
    event_type: str = "risk_assessment.created"
    aggregate_type: str = "risk_assessment"
    risk_assessment_id: RiskAssessmentId
    hazard_id: HazardId


class RiskAssessmentUpdated(SafetyDomainEvent):
    event_type: str = "risk_assessment.updated"
    aggregate_type: str = "risk_assessment"
    risk_assessment_id: RiskAssessmentId


class RiskAssessmentApproved(SafetyDomainEvent):
    event_type: str = "risk_assessment.approved"
    aggregate_type: str = "risk_assessment"
    risk_assessment_id: RiskAssessmentId
    previous_status: str
    new_status: str


class RiskAssessmentSuperseded(SafetyDomainEvent):
    event_type: str = "risk_assessment.superseded"
    aggregate_type: str = "risk_assessment"
    risk_assessment_id: RiskAssessmentId
    superseded_by_id: RiskAssessmentId
    previous_status: str
    new_status: str


class RiskAssessmentArchived(SafetyDomainEvent):
    event_type: str = "risk_assessment.archived"
    aggregate_type: str = "risk_assessment"
    risk_assessment_id: RiskAssessmentId
    previous_status: str
    new_status: str
    reason: str


class RiskControlCreated(SafetyDomainEvent):
    event_type: str = "risk_control.created"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId


class RiskControlUpdated(SafetyDomainEvent):
    event_type: str = "risk_control.updated"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId


class RiskControlPlanned(SafetyDomainEvent):
    event_type: str = "risk_control.planned"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlImplementationStarted(SafetyDomainEvent):
    event_type: str = "risk_control.implementation_started"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlImplementationProgressed(SafetyDomainEvent):
    event_type: str = "risk_control.implementation_progressed"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    progress: int


class RiskControlImplemented(SafetyDomainEvent):
    event_type: str = "risk_control.implemented"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlVerificationRecorded(SafetyDomainEvent):
    event_type: str = "risk_control.verification_recorded"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    result: str


class RiskControlVerifiedEffective(SafetyDomainEvent):
    event_type: str = "risk_control.verified_effective"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlVerifiedPartiallyEffective(SafetyDomainEvent):
    event_type: str = "risk_control.verified_partially_effective"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlVerifiedIneffective(SafetyDomainEvent):
    event_type: str = "risk_control.verified_ineffective"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlReviewScheduled(SafetyDomainEvent):
    event_type: str = "risk_control.review_scheduled"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId


class RiskControlReviewCompleted(SafetyDomainEvent):
    event_type: str = "risk_control.review_completed"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId


class RiskControlOwnerAssigned(SafetyDomainEvent):
    event_type: str = "risk_control.owner_assigned"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    owner_reference: str


class RiskControlOwnerChanged(SafetyDomainEvent):
    event_type: str = "risk_control.owner_changed"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_owner_reference: str | None
    owner_reference: str


class RiskControlSuspended(SafetyDomainEvent):
    event_type: str = "risk_control.suspended"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str
    reason: str


class RiskControlResumed(SafetyDomainEvent):
    event_type: str = "risk_control.resumed"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str


class RiskControlSuperseded(SafetyDomainEvent):
    event_type: str = "risk_control.superseded"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    superseded_by_id: RiskControlId
    previous_status: str
    new_status: str
    reason: str


class RiskControlArchived(SafetyDomainEvent):
    event_type: str = "risk_control.archived"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str
    reason: str


class RiskControlCancelled(SafetyDomainEvent):
    event_type: str = "risk_control.cancelled"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    previous_status: str
    new_status: str
    reason: str


class RiskControlCorrectionRecorded(SafetyDomainEvent):
    event_type: str = "risk_control.correction_recorded"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    target_record_type: str
    target_record_id: str


class RiskReassessmentRecommended(SafetyDomainEvent):
    event_type: str = "risk.reassessment_recommended"
    aggregate_type: str = "risk_control"
    risk_control_id: RiskControlId
    risk_assessment_id: RiskAssessmentId | None = None
    hazard_id: HazardId | None = None
    reason: str = ""


class RiskAssessed(SafetyDomainEvent):
    event_type: str = "risk.assessed"
    aggregate_type: str = "risk"


class RiskAccepted(SafetyDomainEvent):
    event_type: str = "risk.accepted"
    aggregate_type: str = "risk"


class ControlImplemented(SafetyDomainEvent):
    event_type: str = "control.implemented"
    aggregate_type: str = "risk"


class InspectionCompleted(SafetyDomainEvent):
    event_type: str = "inspection.completed"
    aggregate_type: str = "inspection"


class FindingCreated(SafetyDomainEvent):
    event_type: str = "finding.created"
    aggregate_type: str = "inspection"


class IncidentReported(SafetyDomainEvent):
    event_type: str = "incident.reported"
    aggregate_type: str = "incident"


class CorrectiveActionAssigned(SafetyDomainEvent):
    event_type: str = "corrective_action.assigned"
    aggregate_type: str = "corrective_action"


class CorrectiveActionCompleted(SafetyDomainEvent):
    event_type: str = "corrective_action.completed"
    aggregate_type: str = "corrective_action"


class TrainingCompleted(SafetyDomainEvent):
    event_type: str = "training.completed"
    aggregate_type: str = "training"


class PermitIssued(SafetyDomainEvent):
    event_type: str = "permit.issued"
    aggregate_type: str = "permit"


class PermitClosed(SafetyDomainEvent):
    event_type: str = "permit.closed"
    aggregate_type: str = "permit"


class EmergencyActivated(SafetyDomainEvent):
    event_type: str = "emergency.activated"
    aggregate_type: str = "emergency_plan"

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.value_objects import OrganizationId, UserId
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
)
from backend.core.domain.value_objects.safety_enums import (
    ControlCompetencyRequirementType,
    ControlNature,
    ControlOwnerType,
    ControlRelatedEntityType,
    ControlScopeType,
    ControlType,
    EffectivenessResult,
    EvidenceType,
    MilestoneStatus,
    ReviewBasis,
    RiskControlSourceType,
    RiskControlStatus,
    VerificationType,
)
from backend.core.domain.value_objects.safety_ids import (
    HazardId,
    RiskAssessmentId,
    RiskControlId,
)


def make_actor() -> UserId:
    return UserId(value=uuid4())


def make_owner(*, actor: UserId, at: datetime, reference: str = "owner-1") -> ControlOwner:
    return ControlOwner(
        owner_type=ControlOwnerType.USER,
        owner_reference=reference,
        display_name_snapshot="Control Owner",
        assigned_at=at,
        assigned_by=actor,
    )


def risk_control_draft(
    *,
    organization_id: OrganizationId | None = None,
    actor: UserId | None = None,
    code: str | None = None,
    at: datetime | None = None,
    hazard_id: HazardId | None = None,
    risk_assessment_id: RiskAssessmentId | None = None,
    source_control_reference: str | None = None,
) -> RiskControl:
    stamp = at or datetime.now(UTC)
    user = actor or make_actor()
    org = organization_id or OrganizationId(value=uuid4())
    source = ControlSource(
        source_type=(
            RiskControlSourceType.RISK_ASSESSMENT
            if risk_assessment_id is not None
            else RiskControlSourceType.MANAGEMENT_DECISION
        ),
        source_reference=(
            None if risk_assessment_id is None else str(risk_assessment_id.value)
        ),
        risk_assessment_id=risk_assessment_id,
        source_control_reference=source_control_reference,
        assessment_version=3 if risk_assessment_id is not None else None,
        assessment_approved_at=stamp if risk_assessment_id is not None else None,
        residual_level="medium" if risk_assessment_id is not None else None,
        snapshot=(
            {
                "control_type": "engineering",
                "description": "Guard",
            }
        ),
    )
    return RiskControl.create(
        organization_id=org,
        code=code or f"RC-{uuid4().hex[:8]}",
        title="Engineering guard",
        description="Fixed guard around rotating parts",
        hierarchy_level=ControlType.ENGINEERING,
        control_nature=ControlNature.PREVENTIVE,
        source=source,
        created_by=user,
        created_at=stamp,
        hazard_id=hazard_id,
        risk_assessment_id=risk_assessment_id,
        scope=(
            ScopeReference(
                scope_type=ControlScopeType.WORKPLACE,
                reference="Bay-1",
            ),
            ScopeReference(
                scope_type=ControlScopeType.EQUIPMENT,
                reference="CONV-01",
            ),
        ),
        owner=make_owner(actor=user, at=stamp),
        verification_method_requirement="Visual inspection and function test",
        competency_requirements=(
            ControlCompetencyRequirement(
                competency_ref="mechanical_fitter",
                requirement_type=ControlCompetencyRequirementType.MAINTAINER,
                required_level="competent",
                training_program_ref="TR-MECH-01",
                notes="Lockout competence required",
            ),
        ),
        related_entities=(
            RelatedEntityReference(
                entity_type=ControlRelatedEntityType.INSTRUCTION,
                reference="INST-GUARD-01",
            ),
        ),
        extension_data={"country_profile": "ru", "industry": "manufacturing"},
    )


def risk_control_rich_round_trip(
    *,
    organization_id: OrganizationId | None = None,
    actor: UserId | None = None,
) -> RiskControl:
    """Build a fully populated control suitable for persistence round-trip."""

    stamp = datetime.now(UTC)
    user = actor or make_actor()
    control = risk_control_draft(organization_id=organization_id, actor=user, at=stamp)
    planned = control.plan(
        at=stamp,
        actor_id=user,
        expected_version=1,
        implementation=ImplementationPlan(
            target_start_date=stamp,
            target_completion_date=stamp + timedelta(days=14),
            implementation_method="Fabricate and install",
            milestones=(
                ImplementationMilestone(
                    title="Fabricate",
                    description="Cut and weld",
                    due_date=stamp + timedelta(days=7),
                    status=MilestoneStatus.COMPLETED,
                    completed_at=stamp + timedelta(days=5),
                    evidence_refs=("doc://fab",),
                ),
                ImplementationMilestone(
                    title="Install",
                    due_date=stamp + timedelta(days=14),
                    status=MilestoneStatus.IN_PROGRESS,
                ),
            ),
            dependencies=("WO-100",),
            resource_notes="Needs shutdown window",
            evidence_requirements=("photo", "work_order"),
            progress=40,
            summary="Fabrication done",
        ),
    )
    started = planned.start_implementation(at=stamp, actor_id=user, expected_version=2)
    with_evidence = started.add_evidence(
        evidence=EvidenceReference(
            evidence_type=EvidenceType.PHOTO,
            external_reference="doc://photo-1",
            title="Installed guard",
            description="Side view",
            captured_at=stamp,
            captured_by=user,
            checksum="abc123",
            metadata={"camera": "plant"},
        ),
        at=stamp,
        actor_id=user,
        expected_version=3,
    )
    progressed = with_evidence.update_progress(
        at=stamp,
        actor_id=user,
        expected_version=4,
        progress=100,
        summary="Installation complete",
        milestones=(
            ImplementationMilestone(
                title="Fabricate",
                status=MilestoneStatus.COMPLETED,
                completed_at=stamp,
            ),
            ImplementationMilestone(
                title="Install",
                status=MilestoneStatus.COMPLETED,
                completed_at=stamp,
            ),
        ),
    )
    implemented = progressed.complete_implementation(
        at=stamp,
        actor_id=user,
        expected_version=5,
        summary="Guard installed and bolted",
    )
    verified, _ = implemented.record_verification(
        verification=ControlEffectivenessVerification(
            verification_type=VerificationType.INITIAL,
            method="Walkdown",
            criteria="No exposed rotating parts",
            performed_at=stamp,
            performed_by=user,
            result=EffectivenessResult.EFFECTIVE,
            rating="A",
            findings="Compliant",
            evidence_refs=("doc://photo-1",),
            next_action="Periodic review",
            next_review_date=stamp + timedelta(days=365),
            profile_key="default",
            profile_version="1",
        ),
        at=stamp,
        actor_id=user,
        expected_version=6,
    )
    scheduled = verified.schedule_review(
        schedule=ControlReviewSchedule(
            review_required=True,
            review_frequency_days=180,
            next_review_date=stamp + timedelta(days=180),
            last_review_date=stamp,
            review_basis=ReviewBasis.FIXED_INTERVAL,
            escalation_policy_ref="ESC-1",
        ),
        at=stamp,
        actor_id=user,
        expected_version=7,
    )
    return scheduled


def assert_control_domain_equal(left: RiskControl, right: RiskControl) -> None:
    assert left.model_dump(mode="json") == right.model_dump(mode="json")


def advance_to_implemented(control: RiskControl, *, actor: UserId, at: datetime) -> RiskControl:
    planned = control.plan(
        at=at,
        actor_id=actor,
        expected_version=control.version,
        implementation=ImplementationPlan(target_completion_date=at + timedelta(days=7)),
    )
    started = planned.start_implementation(
        at=at, actor_id=actor, expected_version=planned.version
    )
    evidenced = started.add_evidence(
        evidence=EvidenceReference(
            evidence_type=EvidenceType.DOCUMENT,
            external_reference="doc://impl",
            title="Completion note",
            captured_at=at,
            captured_by=actor,
        ),
        at=at,
        actor_id=actor,
        expected_version=started.version,
    )
    return evidenced.complete_implementation(
        at=at,
        actor_id=actor,
        expected_version=evidenced.version,
        summary="Done",
    )


__all__ = [
    "RiskControlId",
    "RiskControlStatus",
    "advance_to_implemented",
    "assert_control_domain_equal",
    "make_actor",
    "make_owner",
    "risk_control_draft",
    "risk_control_rich_round_trip",
]

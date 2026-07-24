from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import (
    InvalidRiskControlTransition,
    RiskControlValidationError,
    RiskControlVersionConflict,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_control_components import (
    ControlEffectivenessVerification,
    ControlOwner,
    ControlSource,
    EvidenceReference,
    ImplementationPlan,
    ScopeReference,
)
from backend.core.domain.value_objects.safety_enums import (
    ControlNature,
    ControlOwnerType,
    ControlScopeType,
    ControlType,
    EffectivenessResult,
    EvidenceType,
    RiskControlSourceType,
    RiskControlStatus,
    VerificationType,
)


def _base(**kwargs):
    now = datetime.now(UTC)
    actor = UserId(value=uuid4())
    defaults = dict(
        organization_id=OrganizationId(value=uuid4()),
        code="RC-1",
        title="Guardrail",
        description="Install fixed guardrail",
        hierarchy_level=ControlType.ENGINEERING,
        control_nature=ControlNature.PREVENTIVE,
        source=ControlSource(source_type=RiskControlSourceType.MANAGEMENT_DECISION),
        created_by=actor,
        created_at=now,
        scope=(
            ScopeReference(
                scope_type=ControlScopeType.WORKPLACE,
                reference="Bay-1",
            ),
        ),
        owner=ControlOwner(
            owner_type=ControlOwnerType.USER,
            owner_reference=str(actor.value),
            display_name_snapshot="Owner",
            assigned_at=now,
            assigned_by=actor,
        ),
        verification_method_requirement="Inspection",
    )
    defaults.update(kwargs)
    return RiskControl.create(**defaults), actor, now


def test_create_and_plan_requires_target_date() -> None:
    control, actor, now = _base()
    assert control.lifecycle_status is RiskControlStatus.DRAFT
    with pytest.raises(RiskControlValidationError):
        control.plan(
            at=now,
            actor_id=actor,
            expected_version=1,
            implementation=ImplementationPlan(),
        )
    planned = control.plan(
        at=now,
        actor_id=actor,
        expected_version=1,
        implementation=ImplementationPlan(
            target_completion_date=now + timedelta(days=30),
        ),
    )
    assert planned.lifecycle_status is RiskControlStatus.PLANNED
    assert planned.version == 2


def test_implementation_to_verified_effective() -> None:
    control, actor, now = _base()
    planned = control.plan(
        at=now,
        actor_id=actor,
        expected_version=1,
        implementation=ImplementationPlan(
            target_completion_date=now + timedelta(days=10),
        ),
    )
    started = planned.start_implementation(
        at=now, actor_id=actor, expected_version=2
    )
    with_evidence = started.add_evidence(
        evidence=EvidenceReference(
            evidence_type=EvidenceType.PHOTO,
            external_reference="doc://1",
            title="Photo",
            captured_at=now,
            captured_by=actor,
        ),
        at=now,
        actor_id=actor,
        expected_version=3,
    )
    implemented = with_evidence.complete_implementation(
        at=now,
        actor_id=actor,
        expected_version=4,
        summary="Installed",
    )
    verified, recommend = implemented.record_verification(
        verification=ControlEffectivenessVerification(
            verification_type=VerificationType.INITIAL,
            method="Walkdown",
            performed_at=now,
            performed_by=actor,
            result=EffectivenessResult.EFFECTIVE,
            evidence_refs=("doc://1",),
            next_review_date=now + timedelta(days=365),
        ),
        at=now,
        actor_id=actor,
        expected_version=5,
    )
    assert verified.lifecycle_status is RiskControlStatus.VERIFIED_EFFECTIVE
    assert recommend is False
    assert verified.latest_effectiveness_result is EffectivenessResult.EFFECTIVE


def test_ineffective_recommends_reassessment_and_version_conflict() -> None:
    control, actor, now = _base()
    planned = control.plan(
        at=now,
        actor_id=actor,
        expected_version=1,
        implementation=ImplementationPlan(target_completion_date=now),
    )
    started = planned.start_implementation(at=now, actor_id=actor, expected_version=2)
    with_evidence = started.add_evidence(
        evidence=EvidenceReference(
            evidence_type=EvidenceType.DOCUMENT,
            external_reference="doc://2",
            title="Report",
            captured_at=now,
            captured_by=actor,
        ),
        at=now,
        actor_id=actor,
        expected_version=3,
    )
    implemented = with_evidence.complete_implementation(
        at=now, actor_id=actor, expected_version=4, summary="Done"
    )
    verified, recommend = implemented.record_verification(
        verification=ControlEffectivenessVerification(
            verification_type=VerificationType.INITIAL,
            method="Test",
            performed_at=now,
            performed_by=actor,
            result=EffectivenessResult.INEFFECTIVE,
            evidence_refs=("doc://2",),
            findings="Failed",
        ),
        at=now,
        actor_id=actor,
        expected_version=5,
    )
    assert recommend is True
    assert verified.lifecycle_status is RiskControlStatus.VERIFIED_INEFFECTIVE
    with pytest.raises(RiskControlVersionConflict):
        verified.cancel(at=now, actor_id=actor, expected_version=5, reason="x")


def test_overdue_and_invalid_transition() -> None:
    control, actor, now = _base()
    scheduled = control.schedule_review(
        schedule=control.review_schedule.model_copy(
            update={"next_review_date": now - timedelta(days=1)}
        ),
        at=now,
        actor_id=actor,
        expected_version=1,
    )
    assert scheduled.is_overdue_for_review(as_of=now) is True
    with pytest.raises(InvalidRiskControlTransition):
        scheduled.start_implementation(at=now, actor_id=actor, expected_version=2)

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.corrective_action import CorrectiveAction
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.inspection import Finding, Inspection
from backend.core.domain.entities.risk import Control, Risk
from backend.core.domain.entities.training_permit_emergency_asset import Permit
from backend.core.domain.events.safety_events import HazardCreated, RiskAssessed
from backend.core.domain.exceptions.hazard import HazardAlreadyActive
from backend.core.domain.exceptions.safety import InvalidSafetyLifecycleTransition
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.hierarchy_of_controls import (
    HIERARCHY_OF_CONTROLS,
    is_preferred_over,
)
from backend.core.domain.value_objects.safety_enums import (
    ControlType,
    CorrectiveActionStatus,
    FindingSeverity,
    HazardCategory,
    HazardSource,
    HazardStatus,
    Probability,
    RiskLevel,
    SafetyDirection,
    Severity,
)
from backend.core.domain.value_objects.safety_ids import (
    ControlId,
    CorrectiveActionId,
    FindingId,
    HazardId,
    InspectionId,
    PermitId,
    RiskId,
)


def test_hierarchy_of_controls_orders_elimination_before_ppe() -> None:
    assert HIERARCHY_OF_CONTROLS[0] is ControlType.ELIMINATION
    assert HIERARCHY_OF_CONTROLS[-1] is ControlType.PPE
    assert is_preferred_over(ControlType.ENGINEERING, ControlType.PPE)
    assert not is_preferred_over(ControlType.PPE, ControlType.ELIMINATION)


def test_hazard_lifecycle_activate_archive_restore() -> None:
    now = datetime.now(UTC)
    hazard = Hazard.create(
        organization_id=OrganizationId(value=uuid4()),
        code="HZ-001",
        title="Unguarded conveyor",
        description="Missing guard",
        category=HazardCategory.PHYSICAL,
        safety_directions=[SafetyDirection.OCCUPATIONAL_SAFETY],
        source=HazardSource.INSPECTION,
        identified_at=now,
        identified_by=UserId(value=uuid4()),
    )
    actor = UserId(value=uuid4())
    active = hazard.activate(at=now + timedelta(seconds=1), reviewed_by=actor)
    assert active.status is HazardStatus.ACTIVE
    with pytest.raises(HazardAlreadyActive):
        active.activate(at=now + timedelta(seconds=2), reviewed_by=actor)
    archived = active.archive(
        at=now + timedelta(seconds=3),
        archived_by=actor,
        reason="Superseded",
    )
    assert archived.status is HazardStatus.ARCHIVED
    restored = archived.restore(
        at=now + timedelta(seconds=4),
        restored_by=actor,
        reason="Still relevant",
    )
    assert restored.status is HazardStatus.ACTIVE
    assert restored.archived_at is not None


def test_risk_assessment_and_control_attachment() -> None:
    now = datetime.now(UTC)
    risk = Risk(
        id=RiskId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        hazard_id=HazardId(value=uuid4()),
        created_at=now,
        updated_at=now,
    )
    assessed = risk.assess(
        probability=Probability.POSSIBLE,
        severity=Severity.MAJOR,
        inherent_level=RiskLevel.HIGH,
        residual_level=RiskLevel.MEDIUM,
        at=now,
    )
    controlled = assessed.with_control(
        Control(
            id=ControlId(value=uuid4()),
            title="Install guard",
            control_type=ControlType.ENGINEERING,
            implemented=True,
        ),
        at=now,
    )
    assert controlled.inherent_level is RiskLevel.HIGH
    assert controlled.residual_level is RiskLevel.MEDIUM
    assert controlled.controls[0].control_type is ControlType.ENGINEERING


def test_inspection_findings_only_while_in_progress() -> None:
    now = datetime.now(UTC)
    inspection = Inspection(
        id=InspectionId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        title="Weekly plant walk",
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(ValueError, match="in progress"):
        inspection.add_finding(
            Finding(
                id=FindingId(value=uuid4()),
                summary="Missing guard",
                severity=FindingSeverity.HIGH,
                created_at=now,
            ),
            at=now,
        )
    started = inspection.start(at=now)
    with_finding = started.add_finding(
        Finding(
            id=FindingId(value=uuid4()),
            summary="Missing guard",
            severity=FindingSeverity.HIGH,
            created_at=now,
        ),
        at=now,
    )
    completed = with_finding.complete(at=now + timedelta(minutes=5))
    assert completed.completed_at is not None
    assert len(completed.findings) == 1


def test_corrective_action_requires_full_verification_path() -> None:
    now = datetime.now(UTC)
    action = CorrectiveAction(
        id=CorrectiveActionId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        title="Replace guard",
        created_at=now,
        updated_at=now,
    )
    assignee = UserId(value=uuid4())
    assigned = action.assign(assignee, at=now)
    started = assigned.start(at=now)
    completed = started.complete(at=now)
    verified = completed.verify(at=now)
    closed = verified.close(at=now)
    assert closed.status is CorrectiveActionStatus.CLOSED
    with pytest.raises(InvalidSafetyLifecycleTransition):
        completed.close(at=now)


def test_permit_issue_validates_window() -> None:
    now = datetime.now(UTC)
    permit = Permit(
        id=PermitId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        title="Hot work bay 2",
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(ValueError, match="validity"):
        permit.issue(valid_from=now, valid_to=now, at=now)
    issued = permit.issue(
        valid_from=now,
        valid_to=now + timedelta(hours=8),
        at=now,
    )
    assert issued.valid_to is not None


def test_safety_domain_event_carries_organization_scope() -> None:
    organization_id = OrganizationId(value=uuid4())
    aggregate_id = uuid4()
    hazard_id = HazardId(value=aggregate_id)
    event = HazardCreated(
        organization_id=organization_id,
        aggregate_id=aggregate_id,
        hazard_id=hazard_id,
        payload={"title": "Sample"},
    )
    assert event.event_type == "hazard.created"
    assert event.organization_id == organization_id
    assessed = RiskAssessed(
        organization_id=organization_id,
        aggregate_id=uuid4(),
        payload={"inherent_level": "high"},
    )
    assert assessed.aggregate_type == "risk"

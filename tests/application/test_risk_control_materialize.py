from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.commands.risk_control_lifecycle import (
    MaterializeRiskAssessmentControlsCommand,
)
from backend.core.application.handlers.materialize_risk_controls import (
    MaterializeRiskAssessmentControlsHandler,
)
from backend.core.contracts.clock import ClockContract
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_control import RiskControlAlreadyMaterialized
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
    ControlMeasure,
    RiskAcceptance,
)
from backend.core.domain.value_objects.risk_control_query import RiskControlQuery
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    ControlType,
    HazardCategory,
    HazardSource,
    RiskAcceptanceDecision,
    SafetyDirection,
)
from backend.core.domain.value_objects.safety_ids import ControlId
from tests.core.audit_test_support import make_admin_audit_stack
from tests.fixtures.risk_controls import risk_control_draft


class _FixedClock(ClockContract):
    def __init__(self, value: datetime) -> None:
        self._value = value

    def now(self) -> datetime:
        return self._value


def test_materialize_rolls_back_when_duplicate_found() -> None:
    now = datetime.now(UTC)
    stack = make_admin_audit_stack()
    org = stack.ctx.authorization_organization_id
    actor = stack.ctx.actor_user_id
    assert org is not None and actor is not None

    hazard = Hazard.create(
        organization_id=org,
        code="HZ-M",
        title="Hazard",
        description="",
        category=HazardCategory.PHYSICAL,
        safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
        source=HazardSource.INSPECTION,
        identified_at=now,
        identified_by=actor,
        created_at=now,
    ).activate(at=now, reviewed_by=actor)
    stack.uow.hazards.add(hazard)

    assessment = RiskAssessment.create(
        organization_id=org,
        hazard_id=hazard.id,
        code="RA-M",
        title="Assessment",
        assessment_profile=AssessmentProfileCode.SIMPLE_3X3,
        assessed_object=AssessedObjectRef(
            object_type=AssessedObjectType.WORKPLACE,
            reference="Bay",
        ),
        assessor_id=actor,
        assessment_date=now,
        created_at=now,
    )
    control_a = ControlMeasure(
        id=ControlId(value=uuid4()),
        control_type=ControlType.ENGINEERING,
        description="Guard",
    )
    control_b = ControlMeasure(
        id=ControlId(value=uuid4()),
        control_type=ControlType.PPE,
        description="Glasses",
    )
    assessment = assessment.update_details(
        at=now,
        expected_version=1,
        controls=(control_a, control_b),
        inherent_risk=assessment.build_evaluation(probability=2, severity=2),
        acceptance=RiskAcceptance(
            decision=RiskAcceptanceDecision.ACCEPTED,
            justification="ok",
            reviewer_id=actor,
        ),
    ).approve(at=now, approved_by=actor, expected_version=2)
    stack.uow.risk_assessments.add(assessment)

    seeded = risk_control_draft(
        organization_id=org,
        actor=actor,
        risk_assessment_id=assessment.id,
        source_control_reference=str(control_b.id.value),
        code="RC-SEEDED",
        hazard_id=hazard.id,
    )
    stack.uow.risk_controls.add(seeded)

    handler = MaterializeRiskAssessmentControlsHandler(
        stack.uow,
        _FixedClock(now),
        stack.audit,
    )
    with pytest.raises(RiskControlAlreadyMaterialized):
        handler.handle(
            MaterializeRiskAssessmentControlsCommand(
                organization_id=org,
                actor_id=actor,
                risk_assessment_id=assessment.id,
                audit_context=stack.ctx,
            )
        )

    codes = {
        item.code.value
        for item in stack.uow.risk_controls.list(
            RiskControlQuery(organization_id=org, include_terminal=True)
        ).items
    }
    assert codes == {"RC-SEEDED"}
    loaded = stack.uow.risk_assessments.get(org, assessment.id)
    assert loaded is not None
    assert loaded.version == assessment.version
    assert loaded.controls == assessment.controls


def test_materialize_success_preserves_snapshots() -> None:
    now = datetime.now(UTC)
    stack = make_admin_audit_stack()
    org = stack.ctx.authorization_organization_id
    actor = stack.ctx.actor_user_id
    assert org is not None and actor is not None

    hazard = Hazard.create(
        organization_id=org,
        code="HZ-M2",
        title="Hazard",
        description="",
        category=HazardCategory.PHYSICAL,
        safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
        source=HazardSource.INSPECTION,
        identified_at=now,
        identified_by=actor,
        created_at=now,
    ).activate(at=now, reviewed_by=actor)
    stack.uow.hazards.add(hazard)
    control = ControlMeasure(
        id=ControlId(value=uuid4()),
        control_type=ControlType.ADMINISTRATIVE,
        description="Procedure",
    )
    assessment = RiskAssessment.create(
        organization_id=org,
        hazard_id=hazard.id,
        code="RA-M2",
        title="Assessment",
        assessment_profile=AssessmentProfileCode.SIMPLE_3X3,
        assessed_object=AssessedObjectRef(
            object_type=AssessedObjectType.WORK_ACTIVITY,
            reference="Hot work",
        ),
        assessor_id=actor,
        assessment_date=now,
        created_at=now,
    )
    assessment = assessment.update_details(
        at=now,
        expected_version=1,
        controls=(control,),
        inherent_risk=assessment.build_evaluation(probability=1, severity=2),
        acceptance=RiskAcceptance(
            decision=RiskAcceptanceDecision.ACCEPTED,
            justification="ok",
            reviewer_id=actor,
        ),
    ).approve(at=now, approved_by=actor, expected_version=2)
    stack.uow.risk_assessments.add(assessment)

    created = MaterializeRiskAssessmentControlsHandler(
        stack.uow,
        _FixedClock(now),
        stack.audit,
    ).handle(
        MaterializeRiskAssessmentControlsCommand(
            organization_id=org,
            actor_id=actor,
            risk_assessment_id=assessment.id,
            audit_context=stack.ctx,
        )
    )
    assert len(created) == 1
    assert created[0].source.snapshot["description"] == "Procedure"
    assert created[0].source.source_control_reference == str(control.id.value)
    loaded = stack.uow.risk_assessments.get(org, assessment.id)
    assert loaded is not None
    assert loaded.controls[0].description == "Procedure"

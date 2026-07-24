from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    HazardCategory,
    HazardSource,
    SafetyDirection,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.hazard_repository import (
    SQLAlchemyHazardRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.risk_assessment_repository import (
    SQLAlchemyRiskAssessmentRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.risk_control_repository import (
    SQLAlchemyRiskControlRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_risk_control_repository_contracts import (
    RiskControlRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def _ensure_related(session, control: RiskControl) -> None:
    ensure_organization(session, control.organization_id)
    ensure_user(session, control.created_by)
    ensure_user(session, control.updated_by)
    if control.owner is not None:
        ensure_user(session, control.owner.assigned_by)
    for record in control.owner_history:
        ensure_user(session, record.changed_by)
        ensure_user(session, record.owner.assigned_by)
    for evidence in control.evidence:
        ensure_user(session, evidence.captured_by)
    for verification in control.verifications:
        ensure_user(session, verification.performed_by)
    if control.suspension is not None:
        ensure_user(session, control.suspension.suspended_by)

    hazards = SQLAlchemyHazardRepository(session)
    assessments = SQLAlchemyRiskAssessmentRepository(session)
    now = datetime.now(UTC)
    actor = control.created_by

    hazard_id = control.hazard_id
    if hazard_id is None and control.risk_assessment_id is not None:
        # Fabricate a hazard so assessment FK can exist.
        from uuid import uuid4

        from backend.core.domain.value_objects.safety_ids import HazardId

        hazard_id = HazardId(value=uuid4())

    if hazard_id is not None and hazards.get(control.organization_id, hazard_id) is None:
        hazard = Hazard.create(
            organization_id=control.organization_id,
            code=f"H-{hazard_id.value.hex[:8]}",
            title="Seed hazard",
            description="",
            category=HazardCategory.PHYSICAL,
            safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
            source=HazardSource.INSPECTION,
            identified_at=now,
            identified_by=actor,
            created_at=now,
            hazard_id=hazard_id,
        ).activate(at=now, reviewed_by=actor)
        hazards.add(hazard)
        session.flush()

    assessment_id = control.risk_assessment_id
    if assessment_id is not None:
        existing = assessments.get(control.organization_id, assessment_id)
        if existing is None:
            assert hazard_id is not None
            assessment = RiskAssessment.create(
                organization_id=control.organization_id,
                hazard_id=hazard_id,
                code=f"RA-{assessment_id.value.hex[:8]}",
                title="Seed assessment",
                assessment_profile=AssessmentProfileCode.SIMPLE_3X3,
                assessed_object=AssessedObjectRef(
                    object_type=AssessedObjectType.WORKPLACE,
                    reference="Seed",
                ),
                assessor_id=actor,
                assessment_date=now,
                created_at=now,
                risk_assessment_id=assessment_id,
            )
            assessments.add(assessment)
            session.flush()


class _SeedingRiskControlRepository(SQLAlchemyRiskControlRepository):
    def add(self, control: RiskControl) -> None:
        _ensure_related(self._session, control)
        # Align hazard_id when only assessment is present.
        if control.risk_assessment_id is not None and control.hazard_id is None:
            assessment = SQLAlchemyRiskAssessmentRepository(self._session).get(
                control.organization_id,
                control.risk_assessment_id,
            )
            if assessment is not None:
                control = control.model_copy(update={"hazard_id": assessment.hazard_id})
        super().add(control)

    def save(self, control: RiskControl, *, expected_version: int) -> None:
        _ensure_related(self._session, control)
        super().save(control, expected_version=expected_version)


@pytest.mark.db
class TestSQLAlchemyRiskControlRepositoryContract(RiskControlRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyRiskControlRepository:
        return _SeedingRiskControlRepository(sqlalchemy_session)

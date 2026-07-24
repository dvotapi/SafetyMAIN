from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.value_objects.safety_enums import (
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
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_risk_assessment_repository_contracts import (
    RiskAssessmentRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingRiskAssessmentRepository(SQLAlchemyRiskAssessmentRepository):
    def add(self, assessment: RiskAssessment) -> None:
        ensure_organization(self._session, assessment.organization_id)
        ensure_user(self._session, assessment.assessor_id)
        hazards = SQLAlchemyHazardRepository(self._session)
        if hazards.get(assessment.organization_id, assessment.hazard_id) is None:
            now = datetime.now(UTC)
            actor = assessment.assessor_id
            hazard = Hazard.create(
                organization_id=assessment.organization_id,
                code=f"H-{assessment.hazard_id.value.hex[:8]}",
                title="Seed hazard",
                description="",
                category=HazardCategory.PHYSICAL,
                safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
                source=HazardSource.INSPECTION,
                identified_at=now,
                identified_by=actor,
                created_at=now,
                hazard_id=assessment.hazard_id,
            )
            active = hazard.activate(at=now, reviewed_by=actor)
            hazards.add(active)
            self._session.flush()
        super().add(assessment)

    def save(self, assessment: RiskAssessment, *, expected_version: int) -> None:
        ensure_organization(self._session, assessment.organization_id)
        ensure_user(self._session, assessment.assessor_id)
        if assessment.approved_by is not None:
            ensure_user(self._session, assessment.approved_by)
        if assessment.archived_by is not None:
            ensure_user(self._session, assessment.archived_by)
        super().save(assessment, expected_version=expected_version)


@pytest.mark.db
class TestSQLAlchemyRiskAssessmentRepositoryContract(
    RiskAssessmentRepositoryContractSuite
):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyRiskAssessmentRepository:
        return _SeedingRiskAssessmentRepository(sqlalchemy_session)

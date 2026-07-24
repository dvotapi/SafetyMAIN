from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessedObjectType,
    AssessmentProfileCode,
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.hazard_repository import (
    SQLAlchemyHazardRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.risk_assessment_repository import (
    SQLAlchemyRiskAssessmentRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
def test_risk_assessment_survives_session_recreation(migrated_engine) -> None:
    session_factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    organization_id = OrganizationId(value=uuid4())
    actor_id = UserId(value=uuid4())
    now = datetime.now(UTC)

    with session_factory() as session:
        ensure_organization(session, organization_id)
        ensure_user(session, actor_id)
        hazard = Hazard.create(
            organization_id=organization_id,
            code=f"HZ-RA-{uuid4().hex[:8]}",
            title="Persisted hazard",
            description="",
            category=HazardCategory.PHYSICAL,
            safety_directions=(SafetyDirection.OCCUPATIONAL_SAFETY,),
            source=HazardSource.INSPECTION,
            identified_at=now,
            identified_by=actor_id,
            created_at=now,
        ).activate(at=now, reviewed_by=actor_id)
        SQLAlchemyHazardRepository(session).add(hazard)
        assessment = RiskAssessment.create(
            organization_id=organization_id,
            hazard_id=hazard.id,
            code=f"RA-RESTART-{uuid4().hex[:8]}",
            title="Persisted assessment",
            assessment_profile=AssessmentProfileCode.SIMPLE_3X3,
            assessed_object=AssessedObjectRef(
                object_type=AssessedObjectType.LOCATION,
                reference="Plant A",
            ),
            assessor_id=actor_id,
            assessment_date=now,
            created_at=now,
        )
        SQLAlchemyRiskAssessmentRepository(session).add(assessment)
        session.commit()
        assessment_id = assessment.id

    with session_factory() as session:
        loaded = SQLAlchemyRiskAssessmentRepository(session).get(
            organization_id,
            assessment_id,
        )
        assert loaded is not None
        assert loaded.title == "Persisted assessment"
        hazard_loaded = SQLAlchemyHazardRepository(session).get(
            organization_id,
            loaded.hazard_id,
        )
        assert hazard_loaded is not None
        assert hazard_loaded.status is HazardStatus.ACTIVE

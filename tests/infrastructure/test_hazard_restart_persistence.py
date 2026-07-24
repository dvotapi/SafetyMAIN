from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.safety_enums import (
    HazardCategory,
    HazardSource,
    HazardStatus,
    SafetyDirection,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.hazard_repository import (
    SQLAlchemyHazardRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
def test_hazard_survives_session_recreation(migrated_engine) -> None:
    session_factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    organization_id = OrganizationId(value=uuid4())
    actor_id = UserId(value=uuid4())
    now = datetime.now(UTC)
    hazard = Hazard.create(
        organization_id=organization_id,
        code=f"HZ-RESTART-{uuid4().hex[:8]}",
        title="Persisted hazard",
        description="Must survive reconnect",
        category=HazardCategory.CHEMICAL,
        safety_directions=(SafetyDirection.ENVIRONMENTAL_SAFETY,),
        source=HazardSource.ENVIRONMENTAL_MONITORING,
        identified_at=now,
        identified_by=actor_id,
        created_at=now,
    )

    with session_factory() as session:
        ensure_organization(session, organization_id)
        ensure_user(session, actor_id)
        SQLAlchemyHazardRepository(session).add(hazard)
        session.commit()

    with session_factory() as session:
        loaded = SQLAlchemyHazardRepository(session).get(organization_id, hazard.id)
        assert loaded is not None
        assert loaded.code.value == hazard.code.value
        assert loaded.status is HazardStatus.DRAFT
        assert loaded.safety_directions == (SafetyDirection.ENVIRONMENTAL_SAFETY,)

from __future__ import annotations

import pytest

from backend.core.domain.entities.hazard import Hazard
from backend.core.infrastructure.persistence.sqlalchemy.repositories.hazard_repository import (
    SQLAlchemyHazardRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_hazard_repository_contracts import (
    HazardRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingHazardRepository(SQLAlchemyHazardRepository):
    def add(self, hazard: Hazard) -> None:
        ensure_organization(self._session, hazard.organization_id)
        ensure_user(self._session, hazard.identified_by)
        if hazard.reviewed_by is not None:
            ensure_user(self._session, hazard.reviewed_by)
        if hazard.archived_by is not None:
            ensure_user(self._session, hazard.archived_by)
        super().add(hazard)

    def save(self, hazard: Hazard, *, expected_version: int) -> None:
        ensure_organization(self._session, hazard.organization_id)
        ensure_user(self._session, hazard.identified_by)
        if hazard.reviewed_by is not None:
            ensure_user(self._session, hazard.reviewed_by)
        if hazard.archived_by is not None:
            ensure_user(self._session, hazard.archived_by)
        super().save(hazard, expected_version=expected_version)


@pytest.mark.db
class TestSQLAlchemyHazardRepositoryContract(HazardRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyHazardRepository:
        return _SeedingHazardRepository(sqlalchemy_session)

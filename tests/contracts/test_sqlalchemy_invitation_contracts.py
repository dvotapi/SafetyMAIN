from __future__ import annotations

import pytest

from backend.core.infrastructure.persistence.sqlalchemy.repositories.invitation_repository import (
    SQLAlchemyInvitationRepository,
)
from tests.contracts.test_invitation_repository_contracts import InvitationRepositoryContractSuite

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
class TestSQLAlchemyInvitationRepositoryContract(InvitationRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyInvitationRepository:
        return SQLAlchemyInvitationRepository(sqlalchemy_session)

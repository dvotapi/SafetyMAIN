from __future__ import annotations

import pytest

from backend.core.domain.entities.invitation import Invitation
from backend.core.infrastructure.persistence.sqlalchemy.repositories.invitation_repository import (
    SQLAlchemyInvitationRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_invitation_repository_contracts import (
    InvitationRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingInvitationRepository(SQLAlchemyInvitationRepository):
    def add(self, invitation: Invitation) -> None:
        ensure_organization(self._session, invitation.organization_id)
        ensure_user(self._session, invitation.created_by)
        super().add(invitation)


@pytest.mark.db
class TestSQLAlchemyInvitationRepositoryContract(InvitationRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyInvitationRepository:
        return _SeedingInvitationRepository(sqlalchemy_session)

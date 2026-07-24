from __future__ import annotations

import pytest

from backend.core.domain.entities.invitation import Invitation
from backend.core.domain.entities.membership import Membership
from backend.core.infrastructure.persistence.sqlalchemy.repositories.invitation_repository import (
    SQLAlchemyInvitationRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.organization_repository import (
    SQLAlchemyOrganizationRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_identity_repository_contracts import (
    MembershipRepositoryContractSuite,
    OrganizationRepositoryContractSuite,
    UserRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingInvitationRepository(SQLAlchemyInvitationRepository):
    def add(self, invitation: Invitation) -> None:
        ensure_organization(self._session, invitation.organization_id)
        ensure_user(self._session, invitation.created_by)
        super().add(invitation)


class _SeedingMembershipRepository(SQLAlchemyMembershipRepository):
    def add(self, membership: Membership) -> None:
        ensure_organization(self._session, membership.organization_id)
        ensure_user(self._session, membership.user_id)
        super().add(membership)


@pytest.mark.db
class TestSQLAlchemyUserRepositoryContract(UserRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyUserRepository:
        return SQLAlchemyUserRepository(sqlalchemy_session)


@pytest.mark.db
class TestSQLAlchemyMembershipRepositoryContract(MembershipRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyMembershipRepository:
        return _SeedingMembershipRepository(sqlalchemy_session)


@pytest.mark.db
class TestSQLAlchemyOrganizationRepositoryContract(OrganizationRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyOrganizationRepository:
        return SQLAlchemyOrganizationRepository(sqlalchemy_session)

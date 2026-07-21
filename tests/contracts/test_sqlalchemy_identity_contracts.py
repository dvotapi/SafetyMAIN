from __future__ import annotations

import pytest

from backend.core.infrastructure.persistence.sqlalchemy.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from tests.contracts.test_identity_repository_contracts import (
    MembershipRepositoryContractSuite,
    UserRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.mark.db
class TestSQLAlchemyUserRepositoryContract(UserRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyUserRepository:
        return SQLAlchemyUserRepository(sqlalchemy_session)


@pytest.mark.db
class TestSQLAlchemyMembershipRepositoryContract(MembershipRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> SQLAlchemyMembershipRepository:
        return SQLAlchemyMembershipRepository(sqlalchemy_session)

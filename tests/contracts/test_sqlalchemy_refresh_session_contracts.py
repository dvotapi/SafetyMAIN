from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from backend.core.domain.entities.refresh_token_session import RefreshTokenSession
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.persistence.sqlalchemy.repositories.refresh_token_session_repository import (
    SQLAlchemyRefreshTokenSessionRepository,
)
from tests.contracts.refresh_token_session_repository_contract import (
    RefreshTokenSessionRepositoryContractSuite,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_user

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingRefreshTokenSessionRepository(SQLAlchemyRefreshTokenSessionRepository):
    def add(self, session: RefreshTokenSession) -> None:
        ensure_user(self._session, session.user_id)
        super().add(session)


@pytest.mark.db
class TestSQLAlchemyRefreshTokenSessionRepositoryContract(
    RefreshTokenSessionRepositoryContractSuite,
):
    @pytest.fixture()
    def user_id(self, sqlalchemy_session: Session) -> UserId:
        user_id = UserId(value=uuid4())
        ensure_user(sqlalchemy_session, user_id)
        return user_id

    @pytest.fixture()
    def repository(
        self,
        sqlalchemy_session: Session,
    ) -> SQLAlchemyRefreshTokenSessionRepository:
        return _SeedingRefreshTokenSessionRepository(sqlalchemy_session)

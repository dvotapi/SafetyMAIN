from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.infrastructure.persistence.sqlalchemy.repositories import SQLAlchemyAuditEventRepository
from tests.contracts.audit_event_repository_contract import AuditEventRepositoryContractSuite


pytestmark = pytest.mark.db
pytest_plugins = ("tests.infrastructure.db_fixtures",)


class TestSQLAlchemyAuditEventRepositoryContract(AuditEventRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session: Session) -> AuditEventRepositoryContract:
        return SQLAlchemyAuditEventRepository(sqlalchemy_session)

from __future__ import annotations

import pytest

from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.infrastructure.persistence.in_memory import InMemoryAuditEventRepository
from tests.contracts.audit_event_repository_contract import AuditEventRepositoryContractSuite


class TestInMemoryAuditEventRepositoryContract(AuditEventRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> AuditEventRepositoryContract:
        return InMemoryAuditEventRepository()

from __future__ import annotations

import pytest

from backend.core.infrastructure.persistence.in_memory.refresh_token_session_repository import (
    InMemoryRefreshTokenSessionRepository,
)
from tests.contracts.refresh_token_session_repository_contract import (
    RefreshTokenSessionRepositoryContractSuite,
)


class TestInMemoryRefreshTokenSessionRepositoryContract(
    RefreshTokenSessionRepositoryContractSuite,
):
    @pytest.fixture()
    def repository(self) -> InMemoryRefreshTokenSessionRepository:
        return InMemoryRefreshTokenSessionRepository()

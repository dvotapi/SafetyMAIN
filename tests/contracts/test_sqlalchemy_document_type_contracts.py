from __future__ import annotations

import pytest

from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.repositories.document_type_repository import (
    DocumentTypeRepositoryContract,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.document_type_repository import (
    SQLAlchemyDocumentTypeRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization
from tests.contracts.test_document_type_repository_contracts import (
    DocumentTypeRepositoryContractSuite,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


class _SeedingDocumentTypeRepository(SQLAlchemyDocumentTypeRepository):
    def add(self, document_type: DocumentType) -> None:
        ensure_organization(self._session, document_type.organization_id)
        super().add(document_type)


@pytest.mark.db
class TestSQLAlchemyDocumentTypeRepositoryContract(DocumentTypeRepositoryContractSuite):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> DocumentTypeRepositoryContract:
        return _SeedingDocumentTypeRepository(sqlalchemy_session)

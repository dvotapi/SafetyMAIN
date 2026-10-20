from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.exceptions.compliance_document import (
    DuplicateActiveComplianceDocumentCode,
)
from backend.core.domain.repositories.compliance_document_repository import (
    ComplianceDocumentRepositoryContract,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.infrastructure.persistence.sqlalchemy.repositories.compliance_document_repository import (
    SQLAlchemyComplianceDocumentRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.document_type_repository import (
    SQLAlchemyDocumentTypeRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.contracts.test_compliance_document_repository_contracts import (
    ComplianceDocumentRepositoryContractSuite,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    advance_to_active,
    compliance_document_draft,
    make_document_type,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)

LATER = FIXED_AT + timedelta(hours=1)


def ensure_compliance_document_related(session, document: ComplianceDocument) -> None:
    from backend.core.infrastructure.persistence.sqlalchemy.mappers.compliance_document_mapper import (
        to_model as cd_to_model,
    )

    ensure_organization(session, document.organization_id)
    ensure_user(session, document.created_by)
    ensure_user(session, document.updated_by)
    for file in document.files:
        ensure_user(session, file.uploaded_by)
    types_repo = SQLAlchemyDocumentTypeRepository(session)
    if types_repo.get(document.organization_id, document.document_type_id) is None:
        synthetic = DocumentType.create(
            organization_id=document.organization_id,
            code=f"synthetic-{document.document_type_id.value.hex[:8]}",
            title_ru="Synthetic",
            safety_domain=make_document_type().safety_domain,
            subject_kind=document.subject_kind,
            created_at=datetime.now(UTC),
            document_type_id=document.document_type_id,
        )
        types_repo.add(synthetic)
        session.flush()
    stub_type = types_repo.get(document.organization_id, document.document_type_id)
    assert stub_type is not None
    repo = SQLAlchemyComplianceDocumentRepository(session)
    for ref in (
        document.approved_by_document_id,
        document.supersedes_document_id,
        document.superseded_by_document_id,
    ):
        if ref is None:
            continue
        if repo.get(document.organization_id, ref) is not None:
            continue
        stub = ComplianceDocument.create(
            organization_id=document.organization_id,
            document_type=stub_type,
            code=f"stub-{ref.value.hex[:8]}",
            title=f"Stub {ref.value}",
            created_by=document.created_by,
            created_at=document.created_at,
            document_id=ref,
            subject_id=None if document.subject_kind.value == "organization" else uuid4(),
        )
        session.add(cd_to_model(stub))
        session.flush()


class _SeedingComplianceDocumentRepository(SQLAlchemyComplianceDocumentRepository):
    def add(self, document: ComplianceDocument) -> None:
        ensure_compliance_document_related(self._session, document)
        super().add(document)

    def save(self, document: ComplianceDocument, *, expected_version: int) -> None:
        ensure_compliance_document_related(self._session, document)
        super().save(document, expected_version=expected_version)


@pytest.mark.db
class TestSQLAlchemyComplianceDocumentRepositoryContract(
    ComplianceDocumentRepositoryContractSuite
):
    @pytest.fixture()
    def repository(self, sqlalchemy_session) -> ComplianceDocumentRepositoryContract:
        return _SeedingComplianceDocumentRepository(sqlalchemy_session)


# ------------- additional tests specific to the order of writes (plan review note) --------------


@pytest.fixture()
def _seeded_repository_and_type(sqlalchemy_session):
    document_type = make_document_type()
    ensure_organization(sqlalchemy_session, document_type.organization_id)
    types_repo = SQLAlchemyDocumentTypeRepository(sqlalchemy_session)
    types_repo.add(document_type)
    sqlalchemy_session.flush()
    repo = _SeedingComplianceDocumentRepository(sqlalchemy_session)
    return repo, document_type


@pytest.mark.db
def test_superseded_first_then_new_edition_succeeds(_seeded_repository_and_type) -> None:
    repo, document_type = _seeded_repository_and_type
    old = advance_to_active(
        compliance_document_draft(document_type, code="ИОТ-1"), document_type
    )
    repo.add(old)
    draft = compliance_document_draft(
        document_type, code="ИОТ-1", supersedes_document_id=old.id
    )
    repo.add(draft)
    replacement = advance_to_active(draft, document_type)
    superseded = old.supersede(
        replacement=replacement,
        at=LATER,
        actor_id=old.created_by,
        expected_version=old.version,
    )
    repo.save(superseded, expected_version=old.version)
    repo.save(replacement, expected_version=draft.version)

    loaded_old = repo.get(old.organization_id, old.id)
    loaded_new = repo.get(old.organization_id, replacement.id)
    assert loaded_old is not None and loaded_new is not None
    assert loaded_old.status is ComplianceDocumentStatus.SUPERSEDED
    assert loaded_old.superseded_by_document_id == replacement.id
    assert loaded_new.status is ComplianceDocumentStatus.ACTIVE


@pytest.mark.db
def test_new_edition_before_superseding_is_rejected(_seeded_repository_and_type) -> None:
    repo, document_type = _seeded_repository_and_type
    old = advance_to_active(
        compliance_document_draft(document_type, code="ИОТ-1"), document_type
    )
    repo.add(old)
    draft = compliance_document_draft(
        document_type, code="ИОТ-1", supersedes_document_id=old.id
    )
    repo.add(draft)
    replacement = advance_to_active(draft, document_type)

    with pytest.raises(DuplicateActiveComplianceDocumentCode):
        repo.save(replacement, expected_version=draft.version)

    # After the error the session must still accept the correct order.
    superseded = old.supersede(
        replacement=replacement,
        at=LATER,
        actor_id=old.created_by,
        expected_version=old.version,
    )
    repo.save(superseded, expected_version=old.version)
    repo.save(replacement, expected_version=draft.version)

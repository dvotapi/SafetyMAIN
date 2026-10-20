from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.domain.exceptions.compliance_document import (
    ComplianceDocumentVersionConflict,
)
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.infrastructure.persistence.sqlalchemy.repositories.compliance_document_repository import (
    SQLAlchemyComplianceDocumentRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.document_type_repository import (
    SQLAlchemyDocumentTypeRepository,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization
from tests.contracts.test_sqlalchemy_compliance_document_contracts import (
    _SeedingComplianceDocumentRepository,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    compliance_document_draft,
    make_document_file,
    make_document_type,
    rich_applicability,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)

LATER = FIXED_AT + timedelta(hours=1)


@pytest.mark.db
def test_compliance_document_survives_engine_restart(
    database_url: str, migrated_engine
) -> None:
    document_type = make_document_type()
    factory_a = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    with factory_a() as session:
        ensure_organization(session, document_type.organization_id)
        SQLAlchemyDocumentTypeRepository(session).add(document_type)
        session.flush()

        draft = compliance_document_draft(
            document_type,
            applicability=rich_applicability(),
        )
        # Attach three files at the SAME uploaded_at timestamp.
        file1 = make_document_file(draft, filename="rev-1.pdf", uploaded_at=FIXED_AT)
        file2 = make_document_file(draft, filename="rev-2.pdf", uploaded_at=FIXED_AT)
        file3 = make_document_file(draft, filename="rev-3.pdf", uploaded_at=FIXED_AT)
        actor = draft.created_by
        d1 = draft.attach_file(
            file=file1, at=FIXED_AT, actor_id=actor, expected_version=draft.version
        )
        d2 = d1.attach_file(
            file=file2, at=FIXED_AT, actor_id=actor, expected_version=d1.version
        )
        d3 = d2.attach_file(
            file=file3, at=FIXED_AT, actor_id=actor, expected_version=d2.version
        )
        # Approve, activate, archive to exercise state_before_archive.
        active = (
            d3.approve(at=FIXED_AT, actor_id=actor, expected_version=d3.version)
            .activate(
                document_type=document_type,
                at=FIXED_AT,
                actor_id=actor,
                expected_version=d3.version + 1,
            )
        )
        archived = active.archive(
            at=LATER,
            actor_id=actor,
            expected_version=active.version,
            reason="Withdrawn",
        )

        _SeedingComplianceDocumentRepository(session).add(archived)
        session.commit()
        document_id = archived.id
        expected_dump = archived.model_dump(mode="json")
        expected_file_ids = [f.id.value for f in archived.files]

    migrated_engine.dispose()
    engine_b = create_engine(database_url)
    try:
        factory_b = sessionmaker(bind=engine_b, expire_on_commit=False)
        with factory_b() as session:
            loaded = SQLAlchemyComplianceDocumentRepository(session).get(
                document_type.organization_id, document_id
            )
            assert loaded is not None
            assert loaded.model_dump(mode="json") == expected_dump
            assert loaded.status is ComplianceDocumentStatus.ARCHIVED
            assert loaded.status_before_archive is ComplianceDocumentStatus.ACTIVE
            assert [f.id.value for f in loaded.files] == expected_file_ids
            assert loaded.current_file is not None
            assert loaded.current_file.original_filename == "rev-3.pdf"

            type_loaded = SQLAlchemyDocumentTypeRepository(session).get(
                document_type.organization_id, document_type.id
            )
            assert type_loaded is not None
            assert type_loaded.model_dump(mode="json") == document_type.model_dump(
                mode="json"
            )
    finally:
        engine_b.dispose()


@pytest.mark.db
def test_stale_save_does_not_partially_persist_files(migrated_engine) -> None:
    document_type = make_document_type()
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    with factory() as session:
        ensure_organization(session, document_type.organization_id)
        SQLAlchemyDocumentTypeRepository(session).add(document_type)
        session.flush()
        draft = compliance_document_draft(document_type)
        _SeedingComplianceDocumentRepository(session).add(draft)
        session.commit()
        base_version = draft.version
        document_id = draft.id

    with factory() as session:
        repo = _SeedingComplianceDocumentRepository(session)
        a = repo.get(document_type.organization_id, document_id)
        b = repo.get(document_type.organization_id, document_id)
        assert a is not None and b is not None
        a2 = a.attach_file(
            file=make_document_file(a, filename="first.pdf"),
            at=FIXED_AT,
            actor_id=a.created_by,
            expected_version=a.version,
        )
        repo.save(a2, expected_version=base_version)
        session.commit()

        b2 = b.attach_file(
            file=make_document_file(b, filename="stale.pdf"),
            at=FIXED_AT,
            actor_id=b.created_by,
            expected_version=b.version,
        )
        with pytest.raises(ComplianceDocumentVersionConflict):
            repo.save(b2, expected_version=base_version)
        session.rollback()

    with factory() as session:
        loaded = SQLAlchemyComplianceDocumentRepository(session).get(
            document_type.organization_id, document_id
        )
        assert loaded is not None
        assert [f.original_filename for f in loaded.files] == ["first.pdf"]

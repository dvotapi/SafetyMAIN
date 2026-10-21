from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.value_objects.compliance_enums import ComplianceDocumentStatus
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization
from tests.contracts.test_sqlalchemy_compliance_document_contracts import (
    ensure_compliance_document_related,
)
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    advance_to_active,
    compliance_document_draft,
    make_document_type,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)

LATER = FIXED_AT + timedelta(hours=1)


@pytest.mark.db
def test_unit_of_work_exposes_compliance_repositories_only_inside_context(
    sqlalchemy_session_factory: sessionmaker,
) -> None:
    unit_of_work = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with pytest.raises(RuntimeError):
        _ = unit_of_work.document_types
    with pytest.raises(RuntimeError):
        _ = unit_of_work.compliance_documents

    with unit_of_work:
        assert unit_of_work.document_types is not None
        assert unit_of_work.compliance_documents is not None

    with pytest.raises(RuntimeError):
        _ = unit_of_work.document_types


def _prepare(
    uow: SQLAlchemyUnitOfWork,
    *,
    code: str = "ИОТ-1",
) -> tuple[ComplianceDocument, ComplianceDocument, object]:
    document_type = make_document_type()
    ensure_organization(uow.session, document_type.organization_id)
    uow.document_types.add(document_type)
    uow.session.flush()
    old_active = advance_to_active(
        compliance_document_draft(document_type, code=code), document_type
    )
    ensure_compliance_document_related(uow.session, old_active)
    uow.compliance_documents.add(old_active)
    new_draft = compliance_document_draft(
        document_type, code=code, supersedes_document_id=old_active.id
    )
    ensure_compliance_document_related(uow.session, new_draft)
    uow.compliance_documents.add(new_draft)
    return old_active, new_draft, document_type


@pytest.mark.db
def test_edition_replacement_commits_atomically(
    sqlalchemy_session_factory: sessionmaker,
) -> None:
    uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with uow:
        old_active, new_draft, document_type = _prepare(uow)
        uow.commit()

    replacement_uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with replacement_uow:
        replacement = advance_to_active(new_draft, document_type)
        superseded = old_active.supersede(
            replacement=replacement,
            at=LATER,
            actor_id=old_active.created_by,
            expected_version=old_active.version,
        )
        replacement_uow.compliance_documents.save(
            superseded, expected_version=old_active.version
        )
        replacement_uow.compliance_documents.save(
            replacement, expected_version=new_draft.version
        )
        replacement_uow.commit()

    verify_uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with verify_uow:
        reloaded_old = verify_uow.compliance_documents.get(
            old_active.organization_id, old_active.id
        )
        reloaded_new = verify_uow.compliance_documents.get(
            old_active.organization_id, new_draft.id
        )
        assert reloaded_old is not None and reloaded_new is not None
        assert reloaded_old.status is ComplianceDocumentStatus.SUPERSEDED
        assert reloaded_old.superseded_by_document_id == new_draft.id
        assert reloaded_new.status is ComplianceDocumentStatus.ACTIVE


@pytest.mark.db
def test_edition_replacement_rolls_back_on_error(
    sqlalchemy_session_factory: sessionmaker,
) -> None:
    setup_uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with setup_uow:
        old_active, new_draft, document_type = _prepare(setup_uow)
        setup_uow.commit()

    attempt_uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with pytest.raises(RuntimeError), attempt_uow:
        replacement = advance_to_active(new_draft, document_type)
        superseded = old_active.supersede(
            replacement=replacement,
            at=LATER,
            actor_id=old_active.created_by,
            expected_version=old_active.version,
        )
        attempt_uow.compliance_documents.save(
            superseded, expected_version=old_active.version
        )
        raise RuntimeError("boom")

    verify_uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with verify_uow:
        reloaded_old = verify_uow.compliance_documents.get(
            old_active.organization_id, old_active.id
        )
        reloaded_new = verify_uow.compliance_documents.get(
            old_active.organization_id, new_draft.id
        )
        assert reloaded_old is not None and reloaded_new is not None
        assert reloaded_old.status is ComplianceDocumentStatus.ACTIVE
        assert reloaded_old.version == old_active.version
        assert reloaded_new.status is ComplianceDocumentStatus.DRAFT

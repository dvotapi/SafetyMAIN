from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.compliance_document import ComplianceDocument
from backend.core.domain.entities.document_type import DocumentType
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.compliance_enums import (
    ComplianceDocumentStatus,
    DocumentSubjectKind,
    SafetyDomain,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.compliance_document_mapper import (
    files_to_models,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.compliance_document_mapper import (
    to_model as cd_to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.document_type_mapper import (
    to_model as dt_to_model,
)
from tests.contracts.sqlalchemy_identity_seed import ensure_organization, ensure_user
from tests.fixtures.compliance_documents import (
    FIXED_AT,
    advance_to_active,
    compliance_document_draft,
    make_document_type,
    with_file,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


# -------- helpers --------


def _store_document(
    session: Session,
    *,
    status: ComplianceDocumentStatus = ComplianceDocumentStatus.DRAFT,
    code: str = "DOC-1",
    organization_id: OrganizationId | None = None,
    document_type: DocumentType | None = None,
    attach_file: bool = False,
    subject_id: UUID | None = None,
) -> ComplianceDocument:
    document_type = document_type or make_document_type(organization_id=organization_id)
    ensure_organization(session, document_type.organization_id)
    if (
        session.scalar(
            text("SELECT 1 FROM document_types WHERE id = :id"),
            {"id": document_type.id.value},
        )
        is None
    ):
        session.add(dt_to_model(document_type))
        session.flush()
    extra: dict[str, object] = {}
    if document_type.subject_kind is not DocumentSubjectKind.ORGANIZATION:
        extra["subject_id"] = subject_id or uuid4()
    draft = compliance_document_draft(document_type, code=code, **extra)
    if status is ComplianceDocumentStatus.ACTIVE:
        document = advance_to_active(draft, document_type)
    elif status is ComplianceDocumentStatus.UNDER_REVIEW:
        active = advance_to_active(draft, document_type)
        document = active.start_review(
            at=FIXED_AT, actor_id=active.created_by, expected_version=active.version
        )
    elif attach_file:
        document = with_file(draft)
    else:
        document = draft
    ensure_user(session, document.created_by)
    ensure_user(session, document.updated_by)
    for f in document.files:
        ensure_user(session, f.uploaded_by)
    session.add(cd_to_model(document))
    for fm in files_to_models(document):
        session.add(fm)
    session.flush()
    return document


# -------- archive --------


@pytest.mark.db
@pytest.mark.parametrize(
    "set_status,before,reason,fragment",
    [
        ("archived", None, "'Reason'", "ck_compliance_documents_archive_details"),
        ("archived", "'under_review'", "'Reason'", "ck_compliance_documents_archive_details"),
        ("archived", "'archived'", "'Reason'", "ck_compliance_documents_archive_details"),
        ("draft", "'active'", "'Reason'", "ck_compliance_documents_archive_details"),
        ("draft", None, "'Reason'", "ck_compliance_documents_archive_details"),
    ],
)
def test_archive_details_check(
    sqlalchemy_session, set_status, before, reason, fragment
) -> None:
    doc = _store_document(sqlalchemy_session, status=ComplianceDocumentStatus.DRAFT)
    before_sql = "NULL" if before is None else before
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                f"UPDATE compliance_documents SET status = '{set_status}', "
                f"status_before_archive = {before_sql}, archive_reason = {reason} "
                f"WHERE id = :id"
            ),
            {"id": doc.id.value},
        )
    assert fragment in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_archive_reason_nonempty(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "UPDATE compliance_documents SET status = 'archived', "
                "status_before_archive = 'draft', archive_reason = '   ' "
                "WHERE id = :id"
            ),
            {"id": doc.id.value},
        )
    assert "ck_compliance_documents_archive_reason_nonempty" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


# -------- subject id --------


@pytest.mark.db
def test_subject_id_check_organization_with_subject(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text("UPDATE compliance_documents SET subject_id = :sid WHERE id = :id"),
            {"sid": uuid4(), "id": doc.id.value},
        )
    assert "ck_compliance_documents_subject_id" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_subject_id_check_employee_without_subject(sqlalchemy_session) -> None:
    employee_type = DocumentType.create(
        organization_id=OrganizationId(value=uuid4()),
        code="driver_license",
        title_ru="Driver",
        safety_domain=SafetyDomain.ROAD,
        subject_kind=DocumentSubjectKind.EMPLOYEE,
        validity_months=120,
        created_at=FIXED_AT,
    )
    doc = _store_document(
        sqlalchemy_session,
        organization_id=employee_type.organization_id,
        document_type=employee_type,
    )
    # _store_document inserts a valid employee row (subject_id auto-generated).
    # Attempt to UPDATE subject_id to NULL and confirm the CHECK rejects it.
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text("UPDATE compliance_documents SET subject_kind='employee', subject_id=NULL WHERE id=:id"),
            {"id": doc.id.value},
        )
    assert "ck_compliance_documents_subject_id" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


# -------- self-reference --------


@pytest.mark.db
@pytest.mark.parametrize(
    "column",
    [
        "approved_by_document_id",
        "supersedes_document_id",
        "superseded_by_document_id",
    ],
)
def test_self_reference_check(sqlalchemy_session, column) -> None:
    doc = _store_document(sqlalchemy_session)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(f"UPDATE compliance_documents SET {column} = id WHERE id = :id"),
            {"id": doc.id.value},
        )
    assert "ck_compliance_documents_no_self_reference" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


# -------- D9 partial unique --------


@pytest.mark.db
def test_in_force_code_unique_index_active_vs_active(sqlalchemy_session) -> None:
    doc1 = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    doc2 = _store_document(
        sqlalchemy_session,
        status=ComplianceDocumentStatus.DRAFT,
        code="ИОТ-1",
        organization_id=doc1.organization_id,
        document_type=make_document_type(
            organization_id=doc1.organization_id, code="iot_other"
        ),
    )
    # Promote doc2 directly to active with the same code via raw UPDATE.
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "UPDATE compliance_documents "
                "SET status='active' "
                "WHERE id=:id"
            ),
            {"id": doc2.id.value},
        )
    assert "uq_compliance_documents_org_code_in_force" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_in_force_code_unique_index_active_vs_under_review(sqlalchemy_session) -> None:
    doc1 = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    doc2 = _store_document(
        sqlalchemy_session,
        status=ComplianceDocumentStatus.DRAFT,
        code="ИОТ-1",
        organization_id=doc1.organization_id,
        document_type=make_document_type(
            organization_id=doc1.organization_id, code="iot_other"
        ),
    )
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "UPDATE compliance_documents SET status='under_review' WHERE id=:id"
            ),
            {"id": doc2.id.value},
        )
    assert "uq_compliance_documents_org_code_in_force" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
@pytest.mark.parametrize("other_status", ["draft", "superseded", "archived"])
def test_in_force_code_unique_index_allows_non_in_force(
    sqlalchemy_session, other_status
) -> None:
    doc1 = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    other_type = make_document_type(
        organization_id=doc1.organization_id, code="iot_other"
    )
    other = _store_document(
        sqlalchemy_session,
        status=ComplianceDocumentStatus.DRAFT,
        code="ИОТ-1",
        organization_id=doc1.organization_id,
        document_type=other_type,
    )
    if other_status == "superseded":
        extra = (
            "status_before_archive=NULL, archive_reason=NULL"
        )
    elif other_status == "archived":
        extra = "status_before_archive='draft', archive_reason='r'"
    else:
        extra = "status_before_archive=NULL, archive_reason=NULL"
    sqlalchemy_session.execute(
        text(
            f"UPDATE compliance_documents SET status='{other_status}', {extra} WHERE id=:id"
        ),
        {"id": other.id.value},
    )
    sqlalchemy_session.flush()


@pytest.mark.db
def test_in_force_code_unique_index_allows_other_organization(sqlalchemy_session) -> None:
    doc = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    other = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    assert doc.organization_id != other.organization_id


@pytest.mark.db
def test_restore_conflicts_with_in_force_code(sqlalchemy_session) -> None:
    doc1 = _store_document(
        sqlalchemy_session, status=ComplianceDocumentStatus.ACTIVE, code="ИОТ-1"
    )
    # Make doc1 archived (was active) via UPDATE.
    sqlalchemy_session.execute(
        text(
            "UPDATE compliance_documents SET status='archived', "
            "status_before_archive='active', archive_reason='manual' WHERE id=:id"
        ),
        {"id": doc1.id.value},
    )
    sqlalchemy_session.flush()
    _ = _store_document(
        sqlalchemy_session,
        status=ComplianceDocumentStatus.ACTIVE,
        code="ИОТ-1",
        organization_id=doc1.organization_id,
        document_type=make_document_type(
            organization_id=doc1.organization_id, code="iot_other"
        ),
    )
    # Attempt to restore archived doc1 back to active -- should hit partial unique index.
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "UPDATE compliance_documents SET status='active', "
                "status_before_archive=NULL, archive_reason=NULL WHERE id=:id"
            ),
            {"id": doc1.id.value},
        )
    assert "uq_compliance_documents_org_code_in_force" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


# -------- document_files checks --------


@pytest.mark.db
@pytest.mark.parametrize(
    "sha,fragment",
    [
        ("A" * 64, "ck_document_files_sha256_hex"),
        ("a" * 63, "ck_document_files_sha256_hex"),
        ("g" * 64, "ck_document_files_sha256_hex"),
    ],
)
def test_document_file_sha256_check(sqlalchemy_session, sha, fragment) -> None:
    doc = _store_document(sqlalchemy_session, attach_file=True)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text("UPDATE document_files SET sha256=:s WHERE document_id=:d"),
            {"s": sha, "d": doc.id.value},
        )
    assert fragment in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_file_size_check(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session, attach_file=True)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text("UPDATE document_files SET size_bytes=0 WHERE document_id=:d"),
            {"d": doc.id.value},
        )
    assert "ck_document_files_size_positive" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_file_position_check(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session, attach_file=True)
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text("UPDATE document_files SET position=-1 WHERE document_id=:d"),
            {"d": doc.id.value},
        )
    assert "ck_document_files_position_nonnegative" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_file_unique_position(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session, attach_file=True)
    uploader: UserId = doc.created_by
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "INSERT INTO document_files (id, document_id, position, bucket, key, "
                "size_bytes, content_type, sha256, original_filename, uploaded_at, uploaded_by) "
                "VALUES (:fid, :did, 0, 'b', 'k2', 10, 'application/pdf', :sha, 'x.pdf', :ts, :uid)"
            ),
            {
                "fid": uuid4(),
                "did": doc.id.value,
                "sha": "b" * 64,
                "ts": datetime.now(UTC),
                "uid": uploader.value,
            },
        )
    assert "uq_document_files_document_id_position" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_file_unique_key(sqlalchemy_session) -> None:
    doc = _store_document(sqlalchemy_session, attach_file=True)
    existing_key = doc.current_file.key  # type: ignore[union-attr]
    with pytest.raises(IntegrityError) as exc_info:
        sqlalchemy_session.execute(
            text(
                "INSERT INTO document_files (id, document_id, position, bucket, key, "
                "size_bytes, content_type, sha256, original_filename, uploaded_at, uploaded_by) "
                "VALUES (:fid, :did, 1, 'b', :key, 10, 'application/pdf', :sha, 'x.pdf', :ts, :uid)"
            ),
            {
                "fid": uuid4(),
                "did": doc.id.value,
                "key": existing_key,
                "sha": "c" * 64,
                "ts": datetime.now(UTC),
                "uid": doc.created_by.value,
            },
        )
    assert "uq_document_files_document_id_key" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


# -------- document_types checks --------


def _insert_type_sql(
    session: Session,
    *,
    organization_id: UUID,
    code: str,
    review_period_months: object = None,
    validity_months: object = None,
    periodicity_months: object = None,
    thresholds: str = "[90, 30, 14, 7]",
    safety_domain: str = "occupational",
) -> None:
    ensure_organization(session, OrganizationId(value=organization_id))
    session.execute(
        text(
            "INSERT INTO document_types (id, organization_id, code, title_ru, "
            "safety_domain, subject_kind, review_period_months, validity_months, "
            "periodicity_months, warning_thresholds_days, requires_acknowledgement, "
            "requires_approval_order, legal_basis, legal_basis_reference, is_active, "
            "created_at, updated_at) "
            "VALUES (:id, :org, :code, 't', :sd, 'organization', :rp, :vm, :pm, "
            "CAST(:th AS jsonb), false, false, '', NULL, true, :ts, :ts)"
        ),
        {
            "id": uuid4(),
            "org": organization_id,
            "code": code,
            "sd": safety_domain,
            "rp": review_period_months,
            "vm": validity_months,
            "pm": periodicity_months,
            "th": thresholds,
            "ts": datetime.now(UTC),
        },
    )


@pytest.mark.db
def test_document_type_two_periods_rejected(sqlalchemy_session) -> None:
    org = uuid4()
    with pytest.raises(IntegrityError) as exc_info:
        _insert_type_sql(
            sqlalchemy_session,
            organization_id=org,
            code="c1",
            review_period_months=12,
            validity_months=12,
        )
    assert "ck_document_types_single_period" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_type_period_zero_rejected(sqlalchemy_session) -> None:
    org = uuid4()
    with pytest.raises(IntegrityError) as exc_info:
        _insert_type_sql(
            sqlalchemy_session, organization_id=org, code="c1", review_period_months=0
        )
    assert "ck_document_types_periods_positive" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
@pytest.mark.parametrize("thresholds", ["[]", "{}"])
def test_document_type_empty_thresholds_rejected(sqlalchemy_session, thresholds) -> None:
    org = uuid4()
    with pytest.raises(IntegrityError) as exc_info:
        _insert_type_sql(
            sqlalchemy_session,
            organization_id=org,
            code="c1",
            thresholds=thresholds,
        )
    assert "ck_document_types_warning_thresholds" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()


@pytest.mark.db
def test_document_type_unknown_safety_domain_rejected(sqlalchemy_session) -> None:
    org = uuid4()
    with pytest.raises(IntegrityError) as exc_info:
        _insert_type_sql(
            sqlalchemy_session,
            organization_id=org,
            code="c1",
            safety_domain="made_up",
        )
    assert "ck_document_types_safety_domain" in str(exc_info.value.orig)
    sqlalchemy_session.rollback()



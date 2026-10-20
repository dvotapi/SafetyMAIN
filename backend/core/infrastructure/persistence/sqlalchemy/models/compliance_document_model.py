from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base

_SUBJECT_KINDS = ("organization", "employee", "asset")
_DOC_STATUSES = ("draft", "approved", "active", "under_review", "superseded", "archived")
_DOC_SOURCES = ("manual", "generated", "hr_form")
_ARCHIVABLE_FROM = ("draft", "approved", "active", "superseded")


class ComplianceDocumentModel(Base):
    __tablename__ = "compliance_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{v}'" for v in _DOC_STATUSES) + ")",
            name="ck_compliance_documents_status",
        ),
        CheckConstraint(
            "source IN (" + ", ".join(f"'{v}'" for v in _DOC_SOURCES) + ")",
            name="ck_compliance_documents_source",
        ),
        CheckConstraint(
            "subject_kind IN (" + ", ".join(f"'{v}'" for v in _SUBJECT_KINDS) + ")",
            name="ck_compliance_documents_subject_kind",
        ),
        CheckConstraint(
            "version >= 1", name="ck_compliance_documents_version_positive"
        ),
        CheckConstraint(
            "(status = 'archived') = (status_before_archive IS NOT NULL "
            "AND archive_reason IS NOT NULL) "
            "AND (status_before_archive IS NULL OR status_before_archive IN ("
            + ", ".join(f"'{v}'" for v in _ARCHIVABLE_FROM)
            + "))",
            name="ck_compliance_documents_archive_details",
        ),
        CheckConstraint(
            "archive_reason IS NULL OR btrim(archive_reason) <> ''",
            name="ck_compliance_documents_archive_reason_nonempty",
        ),
        CheckConstraint(
            "(subject_kind = 'organization') = (subject_id IS NULL)",
            name="ck_compliance_documents_subject_id",
        ),
        CheckConstraint(
            "approved_by_document_id IS DISTINCT FROM id "
            "AND supersedes_document_id IS DISTINCT FROM id "
            "AND superseded_by_document_id IS DISTINCT FROM id",
            name="ck_compliance_documents_no_self_reference",
        ),
        Index(
            "uq_compliance_documents_org_code_in_force",
            "organization_id",
            "code",
            unique=True,
            postgresql_where=text("status IN ('active', 'under_review')"),
        ),
        Index(
            "ix_compliance_documents_organization_id_status",
            "organization_id",
            "status",
        ),
        Index(
            "ix_compliance_documents_organization_id_document_type_id",
            "organization_id",
            "document_type_id",
        ),
        Index(
            "ix_compliance_documents_organization_id_next_review_at",
            "organization_id",
            "next_review_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("document_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    subject_kind: Mapped[str] = mapped_column(String(length=32), nullable=False)
    subject_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=True
    )
    code: Mapped[str] = mapped_column(String(length=64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    issued_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_by_document_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("compliance_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    supersedes_document_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("compliance_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    superseded_by_document_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("compliance_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    applicability: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source: Mapped[str] = mapped_column(String(length=32), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    status_before_archive: Mapped[str | None] = mapped_column(
        String(length=32), nullable=True
    )
    archive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class DocumentFileModel(Base):
    __tablename__ = "document_files"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "position", name="uq_document_files_document_id_position"
        ),
        UniqueConstraint(
            "document_id", "key", name="uq_document_files_document_id_key"
        ),
        CheckConstraint("position >= 0", name="ck_document_files_position_nonnegative"),
        CheckConstraint("size_bytes > 0", name="ck_document_files_size_positive"),
        CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_document_files_sha256_hex"
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("compliance_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    bucket: Mapped[str] = mapped_column(String(length=63), nullable=False)
    key: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(length=255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(length=64), nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

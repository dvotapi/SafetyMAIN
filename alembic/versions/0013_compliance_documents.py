from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0013_compliance_documents"
down_revision = "0012_risk_controls"
branch_labels = None
depends_on = None


_SAFETY_DOMAINS = (
    "occupational",
    "industrial",
    "labour",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)
_SUBJECT_KINDS = ("organization", "employee", "asset")
_DOC_STATUSES = ("draft", "approved", "active", "under_review", "superseded", "archived")
_DOC_SOURCES = ("manual", "generated", "hr_form")
# status values that may legitimately precede 'archived' (mirrors domain _TRANSITIONS)
_ARCHIVABLE_FROM = ("draft", "approved", "active", "superseded")


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def upgrade() -> None:
    op.create_table(
        "document_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title_ru", sa.Text(), nullable=False),
        sa.Column("safety_domain", sa.String(length=32), nullable=False),
        sa.Column("subject_kind", sa.String(length=32), nullable=False),
        sa.Column("review_period_months", sa.Integer(), nullable=True),
        sa.Column("validity_months", sa.Integer(), nullable=True),
        sa.Column("periodicity_months", sa.Integer(), nullable=True),
        sa.Column(
            "warning_thresholds_days",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("requires_acknowledgement", sa.Boolean(), nullable=False),
        sa.Column("requires_approval_order", sa.Boolean(), nullable=False),
        sa.Column("legal_basis", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("legal_basis_reference", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            _in_list("safety_domain", _SAFETY_DOMAINS),
            name="ck_document_types_safety_domain",
        ),
        sa.CheckConstraint(
            _in_list("subject_kind", _SUBJECT_KINDS),
            name="ck_document_types_subject_kind",
        ),
        sa.CheckConstraint(
            "(review_period_months IS NULL OR review_period_months > 0) "
            "AND (validity_months IS NULL OR validity_months > 0) "
            "AND (periodicity_months IS NULL OR periodicity_months > 0)",
            name="ck_document_types_periods_positive",
        ),
        sa.CheckConstraint(
            "(CASE WHEN review_period_months IS NOT NULL THEN 1 ELSE 0 END "
            "+ CASE WHEN validity_months IS NOT NULL THEN 1 ELSE 0 END "
            "+ CASE WHEN periodicity_months IS NOT NULL THEN 1 ELSE 0 END) <= 1",
            name="ck_document_types_single_period",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(warning_thresholds_days) = 'array' "
            "AND jsonb_array_length(warning_thresholds_days) > 0",
            name="ck_document_types_warning_thresholds",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "code", name="uq_document_types_organization_id_code"
        ),
    )

    op.create_table(
        "compliance_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_kind", sa.String(length=32), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("next_review_at", sa.Date(), nullable=True),
        sa.Column(
            "approved_by_document_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "supersedes_document_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "superseded_by_document_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "applicability",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("status_before_archive", sa.String(length=32), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            _in_list("status", _DOC_STATUSES), name="ck_compliance_documents_status"
        ),
        sa.CheckConstraint(
            _in_list("source", _DOC_SOURCES), name="ck_compliance_documents_source"
        ),
        sa.CheckConstraint(
            _in_list("subject_kind", _SUBJECT_KINDS),
            name="ck_compliance_documents_subject_kind",
        ),
        sa.CheckConstraint("version >= 1", name="ck_compliance_documents_version_positive"),
        sa.CheckConstraint(
            "(status = 'archived') = (status_before_archive IS NOT NULL "
            "AND archive_reason IS NOT NULL) "
            "AND (status_before_archive IS NULL OR status_before_archive IN ("
            + ", ".join(f"'{v}'" for v in _ARCHIVABLE_FROM)
            + "))",
            name="ck_compliance_documents_archive_details",
        ),
        sa.CheckConstraint(
            "archive_reason IS NULL OR btrim(archive_reason) <> ''",
            name="ck_compliance_documents_archive_reason_nonempty",
        ),
        sa.CheckConstraint(
            "(subject_kind = 'organization') = (subject_id IS NULL)",
            name="ck_compliance_documents_subject_id",
        ),
        sa.CheckConstraint(
            "approved_by_document_id IS DISTINCT FROM id "
            "AND supersedes_document_id IS DISTINCT FROM id "
            "AND superseded_by_document_id IS DISTINCT FROM id",
            name="ck_compliance_documents_no_self_reference",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["document_type_id"], ["document_types.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["approved_by_document_id"],
            ["compliance_documents.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_document_id"],
            ["compliance_documents.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_document_id"],
            ["compliance_documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_compliance_documents_org_code_in_force",
        "compliance_documents",
        ["organization_id", "code"],
        unique=True,
        postgresql_where=sa.text("status IN ('active', 'under_review')"),
    )
    op.create_index(
        "ix_compliance_documents_organization_id_status",
        "compliance_documents",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_compliance_documents_organization_id_document_type_id",
        "compliance_documents",
        ["organization_id", "document_type_id"],
    )
    op.create_index(
        "ix_compliance_documents_organization_id_next_review_at",
        "compliance_documents",
        ["organization_id", "next_review_at"],
    )

    op.create_table(
        "document_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("bucket", sa.String(length=63), nullable=False),
        sa.Column("key", sa.String(length=1024), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_document_files_position_nonnegative"),
        sa.CheckConstraint("size_bytes > 0", name="ck_document_files_size_positive"),
        sa.CheckConstraint(
            "sha256 ~ '^[0-9a-f]{64}$'", name="ck_document_files_sha256_hex"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["compliance_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "position", name="uq_document_files_document_id_position"
        ),
        sa.UniqueConstraint(
            "document_id", "key", name="uq_document_files_document_id_key"
        ),
    )


def downgrade() -> None:
    op.drop_table("document_files")
    op.drop_index(
        "ix_compliance_documents_organization_id_next_review_at",
        table_name="compliance_documents",
    )
    op.drop_index(
        "ix_compliance_documents_organization_id_document_type_id",
        table_name="compliance_documents",
    )
    op.drop_index(
        "ix_compliance_documents_organization_id_status",
        table_name="compliance_documents",
    )
    op.drop_index(
        "uq_compliance_documents_org_code_in_force",
        table_name="compliance_documents",
    )
    op.drop_table("compliance_documents")
    op.drop_table("document_types")

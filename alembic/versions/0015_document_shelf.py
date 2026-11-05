"""Document shelf: sections, subsections, places, and place-document links (TASK-P11-012 phase 2)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0015_document_shelf"
down_revision = "0014_transport_security_domain"
branch_labels = None
depends_on = None

# Literal lists: migrations must not depend on application code that changes later.
_SAFETY_DOMAINS = (
    "occupational",
    "industrial",
    "transport_security",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)
_KEPT_ON = ("organization", "facility", "event", "employee", "asset", "profession")
_OBLIGATION_LEVELS = ("mandatory", "conditional", "recommended")
_CURATED_STATUSES = (
    "present",
    "present_needs_review",
    "in_progress",
    "missing",
    "to_clarify",
)
_EXCLUSION_REASONS = ("not_applicable", "condition_not_met", "duplicate", "other")
_CONFIDENCE = ("verified", "secondary", "unconfirmed", "none")

_EXCLUSION_COLUMNS = (
    "exclusion_reason",
    "exclusion_comment",
    "exclusion_status_before",
    "excluded_by",
    "excluded_at",
)


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def _all_or_none(columns: tuple[str, ...]) -> str:
    all_null = " AND ".join(f"{c} IS NULL" for c in columns)
    all_set = " AND ".join(f"{c} IS NOT NULL" for c in columns)
    return f"({all_null}) OR ({all_set})"


def _uuid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=True), nullable=nullable)


def _timestamp(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def _text(name: str) -> sa.Column:
    return sa.Column(name, sa.Text(), nullable=False, server_default=sa.text("''"))


def upgrade() -> None:
    op.create_table(
        "shelf_sections",
        _uuid("id"),
        _uuid("organization_id"),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("safety_domain", sa.String(length=32), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            _in_list("safety_domain", _SAFETY_DOMAINS),
            name="ck_shelf_sections_safety_domain",
        ),
        sa.CheckConstraint("number BETWEEN 1 AND 99", name="ck_shelf_sections_number_range"),
        sa.CheckConstraint("version > 0", name="ck_shelf_sections_version_positive"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "code", name="uq_shelf_sections_organization_id_code"
        ),
        sa.UniqueConstraint(
            "organization_id", "number", name="uq_shelf_sections_organization_id_number"
        ),
    )

    op.create_table(
        "shelf_subsections",
        _uuid("id"),
        _uuid("organization_id"),
        _uuid("section_id"),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_shelf_subsections_position_nonnegative"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["shelf_sections.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "code", name="uq_shelf_subsections_organization_id_code"
        ),
        sa.UniqueConstraint(
            "section_id", "position", name="uq_shelf_subsections_section_id_position"
        ),
    )

    op.create_table(
        "shelf_slots",
        _uuid("id"),
        _uuid("organization_id"),
        sa.Column("code", sa.String(length=32), nullable=False),
        _uuid("section_id"),
        _uuid("subsection_id"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("short_title", sa.String(length=40), nullable=False),
        sa.Column("document_kind", sa.String(length=64), nullable=False),
        sa.Column("kept_on", sa.String(length=32), nullable=False),
        sa.Column("obligation_level", sa.String(length=32), nullable=False),
        _text("applicability_condition"),
        _text("basis_regulation"),
        _text("basis_clause"),
        _text("basis_quote"),
        sa.Column("basis_source_url", sa.Text(), nullable=True),
        sa.Column("basis_confidence", sa.String(length=16), nullable=False),
        _text("review_cycle_text"),
        sa.Column("review_period_months", sa.Integer(), nullable=True),
        sa.Column("curated_status", sa.String(length=32), nullable=False),
        sa.Column("document_type_code", sa.String(length=64), nullable=True),
        _text("proposed_document_type"),
        _text("responsible_text"),
        _text("legacy_location"),
        _text("notes"),
        _text("package_code"),
        _text("legacy_code"),
        sa.Column("exclusion_reason", sa.String(length=32), nullable=True),
        sa.Column("exclusion_comment", sa.Text(), nullable=True),
        sa.Column("exclusion_status_before", sa.String(length=32), nullable=True),
        _uuid("excluded_by", nullable=True),
        _timestamp("excluded_at", nullable=True),
        sa.Column("import_fingerprint", sa.String(length=128), nullable=True),
        _timestamp("last_imported_at", nullable=True),
        _timestamp("created_at"),
        _uuid("created_by"),
        _timestamp("updated_at"),
        _uuid("updated_by"),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(_in_list("kept_on", _KEPT_ON), name="ck_shelf_slots_kept_on"),
        sa.CheckConstraint(
            _in_list("obligation_level", _OBLIGATION_LEVELS),
            name="ck_shelf_slots_obligation_level",
        ),
        sa.CheckConstraint(
            _in_list("curated_status", _CURATED_STATUSES),
            name="ck_shelf_slots_curated_status",
        ),
        sa.CheckConstraint(
            _in_list("basis_confidence", _CONFIDENCE), name="ck_shelf_slots_basis_confidence"
        ),
        sa.CheckConstraint(
            "exclusion_reason IS NULL OR " + _in_list("exclusion_reason", _EXCLUSION_REASONS),
            name="ck_shelf_slots_exclusion_reason",
        ),
        sa.CheckConstraint(
            "exclusion_status_before IS NULL OR "
            + _in_list("exclusion_status_before", _CURATED_STATUSES),
            name="ck_shelf_slots_exclusion_status_before",
        ),
        sa.CheckConstraint(
            _all_or_none(_EXCLUSION_COLUMNS), name="ck_shelf_slots_exclusion_complete"
        ),
        sa.CheckConstraint(
            "exclusion_comment IS NULL "
            "OR char_length(btrim(exclusion_comment)) BETWEEN 5 AND 1000",
            name="ck_shelf_slots_exclusion_comment_length",
        ),
        sa.CheckConstraint(
            "obligation_level <> 'conditional' OR applicability_condition <> ''",
            name="ck_shelf_slots_condition_required",
        ),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 1 AND 500", name="ck_shelf_slots_title_length"
        ),
        sa.CheckConstraint(
            "char_length(short_title) >= 1", name="ck_shelf_slots_short_title_nonempty"
        ),
        sa.CheckConstraint(
            "review_period_months IS NULL OR review_period_months > 0",
            name="ck_shelf_slots_review_period_positive",
        ),
        sa.CheckConstraint("version > 0", name="ck_shelf_slots_version_positive"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["shelf_sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["subsection_id"], ["shelf_subsections.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["excluded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_shelf_slots_organization_id_code"),
    )
    op.create_index(
        "ix_shelf_slots_organization_id_section_id",
        "shelf_slots",
        ["organization_id", "section_id"],
    )
    op.create_index(
        "ix_shelf_slots_organization_id_subsection_id",
        "shelf_slots",
        ["organization_id", "subsection_id"],
    )

    op.create_table(
        "shelf_slot_documents",
        _uuid("organization_id"),
        _uuid("slot_id"),
        _uuid("document_id"),
        sa.Column("position", sa.Integer(), nullable=False),
        _timestamp("linked_at"),
        _uuid("linked_by"),
        sa.CheckConstraint("position >= 0", name="ck_shelf_slot_documents_position_nonnegative"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["shelf_slots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"], ["compliance_documents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["linked_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("slot_id", "document_id"),
        sa.UniqueConstraint(
            "slot_id", "position", name="uq_shelf_slot_documents_slot_id_position"
        ),
    )
    op.create_index(
        "ix_shelf_slot_documents_organization_id_document_id",
        "shelf_slot_documents",
        ["organization_id", "document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_shelf_slot_documents_organization_id_document_id",
        table_name="shelf_slot_documents",
    )
    op.drop_table("shelf_slot_documents")
    op.drop_index("ix_shelf_slots_organization_id_subsection_id", table_name="shelf_slots")
    op.drop_index("ix_shelf_slots_organization_id_section_id", table_name="shelf_slots")
    op.drop_table("shelf_slots")
    op.drop_table("shelf_subsections")
    op.drop_table("shelf_sections")

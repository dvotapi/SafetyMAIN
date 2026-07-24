from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0012_risk_controls"
down_revision = "0011_risk_assessments"
branch_labels = None
depends_on = None

_STATUSES = (
    "draft",
    "planned",
    "in_implementation",
    "implemented",
    "verified_effective",
    "verified_ineffective",
    "suspended",
    "superseded",
    "archived",
    "cancelled",
)


def upgrade() -> None:
    op.create_table(
        "risk_controls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hierarchy_level", sa.String(length=32), nullable=False),
        sa.Column("control_nature", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_reference", sa.String(length=256), nullable=True),
        sa.Column("hazard_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("risk_assessment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_control_reference", sa.String(length=128), nullable=True),
        sa.Column(
            "source_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "scope",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("owner", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("owner_reference", sa.String(length=256), nullable=True),
        sa.Column(
            "owner_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "implementation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "verifications",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "review_schedule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "competency_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "related_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "extension_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("lifecycle_status", sa.String(length=32), nullable=False),
        sa.Column("latest_effectiveness_result", sa.String(length=32), nullable=True),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification_method_requirement",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("suspension", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_before_suspension", sa.String(length=32), nullable=True),
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "btrim(title) <> ''",
            name="ck_risk_controls_title_nonempty",
        ),
        sa.CheckConstraint(
            "lifecycle_status IN (" + ", ".join(f"'{s}'" for s in _STATUSES) + ")",
            name="ck_risk_controls_lifecycle_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_risk_controls_version_positive"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hazard_id"],
            ["safety_hazards.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["risk_assessment_id"],
            ["risk_assessments.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_risk_controls_organization_id_code",
        ),
    )
    op.create_index(
        "uq_risk_controls_org_assessment_source_ref",
        "risk_controls",
        ["organization_id", "risk_assessment_id", "source_control_reference"],
        unique=True,
        postgresql_where=sa.text(
            "source_control_reference IS NOT NULL AND risk_assessment_id IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_risk_controls_organization_id",
        "risk_controls",
        ["organization_id"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_lifecycle_status",
        "risk_controls",
        ["organization_id", "lifecycle_status"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_hazard_id",
        "risk_controls",
        ["organization_id", "hazard_id"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_risk_assessment_id",
        "risk_controls",
        ["organization_id", "risk_assessment_id"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_owner_reference",
        "risk_controls",
        ["organization_id", "owner_reference"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_next_review_date",
        "risk_controls",
        ["organization_id", "next_review_date"],
    )
    op.create_index(
        "ix_risk_controls_organization_id_latest_effectiveness_result",
        "risk_controls",
        ["organization_id", "latest_effectiveness_result"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_risk_controls_organization_id_latest_effectiveness_result",
        table_name="risk_controls",
    )
    op.drop_index(
        "ix_risk_controls_organization_id_next_review_date",
        table_name="risk_controls",
    )
    op.drop_index(
        "ix_risk_controls_organization_id_owner_reference",
        table_name="risk_controls",
    )
    op.drop_index(
        "ix_risk_controls_organization_id_risk_assessment_id",
        table_name="risk_controls",
    )
    op.drop_index(
        "ix_risk_controls_organization_id_hazard_id",
        table_name="risk_controls",
    )
    op.drop_index(
        "ix_risk_controls_organization_id_lifecycle_status",
        table_name="risk_controls",
    )
    op.drop_index("ix_risk_controls_organization_id", table_name="risk_controls")
    op.drop_index(
        "uq_risk_controls_org_assessment_source_ref",
        table_name="risk_controls",
    )
    op.drop_table("risk_controls")

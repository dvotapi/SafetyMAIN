from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011_risk_assessments"
down_revision = "0010_safety_hazards"
branch_labels = None
depends_on = None

_STATUSES = (
    "draft",
    "under_review",
    "approved",
    "superseded",
    "archived",
)


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hazard_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("assessment_profile", sa.String(length=64), nullable=False),
        sa.Column("assessed_object_type", sa.String(length=64), nullable=False),
        sa.Column("assessed_object_reference", sa.String(length=256), nullable=False),
        sa.Column("assessor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "review_schedule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("inherent_risk", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("residual_risk", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "controls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("acceptance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "competency_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "extension_references",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "btrim(title) <> ''",
            name="ck_risk_assessments_title_nonempty",
        ),
        sa.CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in _STATUSES) + ")",
            name="ck_risk_assessments_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_risk_assessments_version_positive"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hazard_id"],
            ["safety_hazards.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assessor_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["archived_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_risk_assessments_organization_id_code",
        ),
    )
    op.create_index(
        "ix_risk_assessments_organization_id",
        "risk_assessments",
        ["organization_id"],
    )
    op.create_index(
        "ix_risk_assessments_organization_id_status",
        "risk_assessments",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_risk_assessments_organization_id_hazard_id",
        "risk_assessments",
        ["organization_id", "hazard_id"],
    )
    op.create_index(
        "ix_risk_assessments_organization_id_profile",
        "risk_assessments",
        ["organization_id", "assessment_profile"],
    )
    op.create_index(
        "ix_risk_assessments_organization_id_created_at",
        "risk_assessments",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_risk_assessments_active_scope",
        "risk_assessments",
        [
            "organization_id",
            "hazard_id",
            "assessment_profile",
            "assessed_object_type",
            "assessed_object_reference",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_risk_assessments_active_scope", table_name="risk_assessments")
    op.drop_index(
        "ix_risk_assessments_organization_id_created_at",
        table_name="risk_assessments",
    )
    op.drop_index(
        "ix_risk_assessments_organization_id_profile",
        table_name="risk_assessments",
    )
    op.drop_index(
        "ix_risk_assessments_organization_id_hazard_id",
        table_name="risk_assessments",
    )
    op.drop_index(
        "ix_risk_assessments_organization_id_status",
        table_name="risk_assessments",
    )
    op.drop_index("ix_risk_assessments_organization_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")

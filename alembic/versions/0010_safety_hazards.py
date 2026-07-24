from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0010_safety_hazards"
down_revision = "0009_refresh_token_sessions"
branch_labels = None
depends_on = None

_HAZARD_STATUSES = (
    "draft",
    "active",
    "archived",
)

_HAZARD_CATEGORIES = (
    "physical",
    "mechanical",
    "electrical",
    "chemical",
    "biological",
    "ergonomic",
    "psychosocial",
    "fire_and_explosion",
    "thermal",
    "radiation",
    "pressure",
    "work_at_height",
    "confined_space",
    "transport",
    "environmental",
    "dangerous_goods",
    "process_safety",
    "natural_hazard",
    "organizational",
    "other",
)


def upgrade() -> None:
    op.create_table(
        "safety_hazards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column(
            "safety_directions",
            postgresql.ARRAY(sa.String(length=64)),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "affected_subjects",
            postgresql.ARRAY(sa.String(length=64)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("location_reference", sa.String(length=512), nullable=True),
        sa.Column("process_reference", sa.String(length=512), nullable=True),
        sa.Column("equipment_reference", sa.String(length=512), nullable=True),
        sa.Column(
            "extension_references",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("identified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("identified_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("btrim(title) <> ''", name="ck_safety_hazards_title_nonempty"),
        sa.CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in _HAZARD_STATUSES) + ")",
            name="ck_safety_hazards_status",
        ),
        sa.CheckConstraint(
            "category IN (" + ", ".join(f"'{c}'" for c in _HAZARD_CATEGORIES) + ")",
            name="ck_safety_hazards_category",
        ),
        sa.CheckConstraint("version >= 1", name="ck_safety_hazards_version_positive"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["identified_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["archived_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "code",
            name="uq_safety_hazards_organization_id_code",
        ),
    )
    op.create_index(
        "ix_safety_hazards_organization_id",
        "safety_hazards",
        ["organization_id"],
    )
    op.create_index(
        "ix_safety_hazards_organization_id_status",
        "safety_hazards",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_safety_hazards_organization_id_category",
        "safety_hazards",
        ["organization_id", "category"],
    )
    op.create_index(
        "ix_safety_hazards_organization_id_created_at",
        "safety_hazards",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_safety_hazards_organization_id_identified_at",
        "safety_hazards",
        ["organization_id", "identified_at"],
    )
    op.create_index(
        "ix_safety_hazards_safety_directions",
        "safety_hazards",
        ["safety_directions"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_safety_hazards_affected_subjects",
        "safety_hazards",
        ["affected_subjects"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_safety_hazards_affected_subjects", table_name="safety_hazards")
    op.drop_index("ix_safety_hazards_safety_directions", table_name="safety_hazards")
    op.drop_index(
        "ix_safety_hazards_organization_id_identified_at",
        table_name="safety_hazards",
    )
    op.drop_index(
        "ix_safety_hazards_organization_id_created_at",
        table_name="safety_hazards",
    )
    op.drop_index(
        "ix_safety_hazards_organization_id_category",
        table_name="safety_hazards",
    )
    op.drop_index(
        "ix_safety_hazards_organization_id_status",
        table_name="safety_hazards",
    )
    op.drop_index("ix_safety_hazards_organization_id", table_name="safety_hazards")
    op.drop_table("safety_hazards")

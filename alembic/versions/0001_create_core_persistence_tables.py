from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0001_create_core_persistence_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_type", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_objects_organization_id",
        "knowledge_objects",
        ["organization_id"],
    )
    op.create_index(
        "ix_knowledge_objects_object_type",
        "knowledge_objects",
        ["object_type"],
    )
    op.create_index("ix_knowledge_objects_status", "knowledge_objects", ["status"])
    op.create_index(
        "ix_knowledge_objects_search_order",
        "knowledge_objects",
        ["organization_id", "created_at", "id"],
    )

    op.create_table(
        "knowledge_object_versions",
        sa.Column("history_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "knowledge_object_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_type", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["knowledge_object_id"],
            ["knowledge_objects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("history_id"),
        sa.UniqueConstraint(
            "knowledge_object_id",
            "version",
            name="uq_knowledge_object_versions_object_version",
        ),
    )
    op.create_index(
        "ix_knowledge_object_versions_history_order",
        "knowledge_object_versions",
        ["knowledge_object_id", "version"],
    )
    op.create_index(
        "ix_knowledge_object_versions_organization_id",
        "knowledge_object_versions",
        ["organization_id"],
    )

    op.create_table(
        "knowledge_object_relations",
        sa.Column("relation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_object_id <> target_object_id",
            name="ck_knowledge_object_relations_no_self_reference",
        ),
        sa.ForeignKeyConstraint(
            ["source_object_id"],
            ["knowledge_objects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_object_id"],
            ["knowledge_objects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("relation_id"),
        sa.UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_object_id",
            "relation_type",
            name="uq_knowledge_object_relations_directed",
        ),
    )
    op.create_index(
        "ix_knowledge_object_relations_outgoing",
        "knowledge_object_relations",
        ["organization_id", "source_object_id", "relation_type", "created_at", "relation_id"],
    )
    op.create_index(
        "ix_knowledge_object_relations_incoming",
        "knowledge_object_relations",
        ["organization_id", "target_object_id", "relation_type", "created_at", "relation_id"],
    )
    op.create_index(
        "ix_knowledge_object_relations_organization_id",
        "knowledge_object_relations",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_object_relations_organization_id",
        table_name="knowledge_object_relations",
    )
    op.drop_index(
        "ix_knowledge_object_relations_incoming",
        table_name="knowledge_object_relations",
    )
    op.drop_index(
        "ix_knowledge_object_relations_outgoing",
        table_name="knowledge_object_relations",
    )
    op.drop_table("knowledge_object_relations")

    op.drop_index(
        "ix_knowledge_object_versions_organization_id",
        table_name="knowledge_object_versions",
    )
    op.drop_index(
        "ix_knowledge_object_versions_history_order",
        table_name="knowledge_object_versions",
    )
    op.drop_table("knowledge_object_versions")

    op.drop_index("ix_knowledge_objects_search_order", table_name="knowledge_objects")
    op.drop_index("ix_knowledge_objects_status", table_name="knowledge_objects")
    op.drop_index("ix_knowledge_objects_object_type", table_name="knowledge_objects")
    op.drop_index(
        "ix_knowledge_objects_organization_id",
        table_name="knowledge_objects",
    )
    op.drop_table("knowledge_objects")


def get_revision_identifiers() -> Sequence[str]:
    return (revision,)

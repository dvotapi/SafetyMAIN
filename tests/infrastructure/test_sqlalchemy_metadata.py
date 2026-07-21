from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from backend.core.infrastructure.persistence.sqlalchemy.base import Base
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectModel,
    KnowledgeObjectRelationModel,
    KnowledgeObjectVersionModel,
)


def test_metadata_contains_required_tables() -> None:
    assert {
        "knowledge_objects",
        "knowledge_object_versions",
        "knowledge_object_relations",
        "users",
        "organizations",
        "memberships",
    }.issubset(Base.metadata.tables)


def test_knowledge_object_columns_and_types() -> None:
    table = KnowledgeObjectModel.__table__

    assert _column_names(table) == {
        "id",
        "organization_id",
        "object_type",
        "status",
        "version",
        "metadata",
        "created_at",
        "updated_at",
    }
    assert isinstance(table.c.id.type, PostgreSQLUUID)
    assert isinstance(table.c.organization_id.type, PostgreSQLUUID)
    assert isinstance(table.c.metadata.type, JSONB)
    assert table.c.created_at.type.timezone is True
    assert table.c.updated_at.type.timezone is True


def test_identity_columns_exist() -> None:
    users = Base.metadata.tables["users"].c
    organizations = Base.metadata.tables["organizations"].c
    memberships = Base.metadata.tables["memberships"].c

    assert {"id", "email", "password_hash", "is_active", "created_at", "updated_at"}.issubset(
        set(users.keys())
    )
    assert {"id", "name", "created_at", "updated_at"}.issubset(set(organizations.keys()))
    assert {
        "id",
        "user_id",
        "organization_id",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }.issubset(set(memberships.keys()))


def test_knowledge_object_version_columns_exist() -> None:
    table = KnowledgeObjectVersionModel.__table__

    assert {
        "history_id",
        "knowledge_object_id",
        "organization_id",
        "object_type",
        "status",
        "version",
        "metadata",
        "created_at",
        "updated_at",
        "recorded_at",
    }.issubset(_column_names(table))
    assert isinstance(table.c.metadata.type, JSONB)


def test_relation_constraints_exist() -> None:
    table = KnowledgeObjectRelationModel.__table__
    unique_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    check_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "uq_knowledge_object_relations_directed" in unique_constraints
    assert "ck_knowledge_object_relations_no_self_reference" in check_constraints


def test_expected_indexes_exist() -> None:
    index_names = {
        index.name
        for table in Base.metadata.tables.values()
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert {
        "ix_memberships_user_id_is_active",
        "ix_memberships_user_id",
        "ix_memberships_organization_id",
        "ix_users_email",
        "ix_knowledge_objects_organization_id",
        "ix_knowledge_objects_object_type",
        "ix_knowledge_objects_status",
        "ix_knowledge_objects_search_order",
        "ix_knowledge_object_versions_history_order",
        "ix_knowledge_object_versions_organization_id",
        "ix_knowledge_object_relations_outgoing",
        "ix_knowledge_object_relations_incoming",
        "ix_knowledge_object_relations_organization_id",
    }.issubset(index_names)


def _column_names(table) -> set[str]:
    return set(table.c.keys())

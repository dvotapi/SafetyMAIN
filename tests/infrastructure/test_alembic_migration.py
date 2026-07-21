from __future__ import annotations

import os
from importlib import util
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_alembic_migration_imports() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "0001_create_core_persistence_tables.py"
    )
    spec = util.spec_from_file_location("migration_0001", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "0001_core_persistence"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "0002_create_identity_tables.py"
    )
    spec = util.spec_from_file_location("migration_0002", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration.revision == "0002_identity_persistence"
    assert migration.down_revision == "0001_core_persistence"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


@pytest.mark.db
def test_apply_and_downgrade_initial_migration_when_database_available() -> None:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run database migration smoke tests.")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for database migration smoke tests.")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    engine = create_engine(database_url)

    command.upgrade(config, "head")
    inspector = inspect(engine)
    assert {
        "knowledge_objects",
        "knowledge_object_versions",
        "knowledge_object_relations",
        "users",
        "organizations",
        "memberships",
    }.issubset(inspector.get_table_names())

    command.downgrade(config, "base")
    inspector = inspect(engine)
    assert "knowledge_objects" not in inspector.get_table_names()

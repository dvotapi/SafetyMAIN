"""Migration 0016_document_file_role (TASK-P11-012 phase 4)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command

pytest_plugins = ("tests.infrastructure.db_fixtures",)

MIGRATION = Path("alembic/versions/0016_document_file_role.py")


def test_migration_revisions() -> None:
    spec = importlib.util.spec_from_file_location("m0016", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0016_document_file_role"
    assert module.down_revision == "0015_document_shelf"


@pytest.mark.db
def test_role_column_default_check_and_downgrade(database_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    engine = create_engine(database_url)
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "0016_document_file_role")
        columns = {c["name"]: c for c in inspect(engine).get_columns("document_files")}
        assert "role" in columns
        assert not columns["role"]["nullable"]
        assert "working" in str(columns["role"]["default"])
        checks = {c["name"]: c["sqltext"] for c in inspect(engine).get_check_constraints("document_files")}
        assert "signed_scan" in checks["ck_document_files_role"]

        command.downgrade(config, "0015_document_shelf")
        columns = {c["name"] for c in inspect(engine).get_columns("document_files")}
        assert "role" not in columns
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar() == 1
    finally:
        command.downgrade(config, "base")
        engine.dispose()

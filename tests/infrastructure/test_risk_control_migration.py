from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def test_0012_risk_controls_migration_module() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "0012_risk_controls.py"
    )
    spec = util.spec_from_file_location("migration_0012", migration_path)
    assert spec is not None and spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0012_risk_controls"
    assert migration.down_revision == "0011_risk_assessments"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


@pytest.mark.db
def test_0012_risk_controls_schema(migrated_engine) -> None:
    inspector = inspect(migrated_engine)
    assert "risk_controls" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("risk_controls")}
    required = {
        "id",
        "organization_id",
        "code",
        "title",
        "description",
        "hierarchy_level",
        "control_nature",
        "source_type",
        "source_control_reference",
        "source_payload",
        "scope",
        "owner",
        "owner_history",
        "implementation",
        "evidence",
        "verifications",
        "review_schedule",
        "lifecycle_status",
        "latest_effectiveness_result",
        "next_review_date",
        "extension_data",
        "version",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
    }
    assert required.issubset(columns)
    indexes = {index["name"] for index in inspector.get_indexes("risk_controls")}
    assert "ix_risk_controls_organization_id_lifecycle_status" in indexes
    assert "uq_risk_controls_org_assessment_source_ref" in indexes
    uniques = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("risk_controls")
    }
    assert "uq_risk_controls_organization_id_code" in uniques
    with migrated_engine.connect() as connection:
        heads = connection.execute(text("SELECT version_num FROM alembic_version")).all()
    assert len(heads) == 1
    assert heads[0][0] == "0012_risk_controls"

from __future__ import annotations

from importlib import util
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from alembic import command

pytest_plugins = ("tests.infrastructure.db_fixtures",)


_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "0014_transport_security_domain.py"
)


def test_0014_transport_security_domain_migration_module() -> None:
    spec = util.spec_from_file_location("migration_0014", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0014_transport_security_domain"
    assert migration.down_revision == "0013_compliance_documents"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


def _insert_document_type(
    engine: Engine, organization_id: UUID, code: str, safety_domain: str
) -> UUID:
    type_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO document_types (id, organization_id, code, title_ru, "
                "safety_domain, subject_kind, warning_thresholds_days, "
                "requires_acknowledgement, requires_approval_order, is_active, "
                "created_at, updated_at) VALUES (:id, :org, :code, 'Тип', :domain, "
                "'organization', '[90, 30, 14, 7]'::jsonb, false, false, true, "
                "now(), now())"
            ),
            {"id": type_id, "org": organization_id, "code": code, "domain": safety_domain},
        )
    return type_id


def _safety_domain(engine: Engine, type_id: UUID) -> str:
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT safety_domain FROM document_types WHERE id = :id"),
            {"id": type_id},
        ).scalar_one()


@pytest.mark.db
def test_0014_converts_labour_rows_and_downgrade_restores_them(
    database_url: str, migrated_engine: Engine
) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "0013_compliance_documents")

    organization_id = uuid4()
    with migrated_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO organizations (id, name, is_active, created_at, updated_at) "
                "VALUES (:id, 'Org', true, now(), now())"
            ),
            {"id": organization_id},
        )
    labour_type = _insert_document_type(
        migrated_engine, organization_id, "trbez_plan", "labour"
    )
    fire_type = _insert_document_type(migrated_engine, organization_id, "fire_plan", "fire")

    command.upgrade(config, "0014_transport_security_domain")
    assert _safety_domain(migrated_engine, labour_type) == "transport_security"
    assert _safety_domain(migrated_engine, fire_type) == "fire"
    with pytest.raises(IntegrityError, match="ck_document_types_safety_domain"):
        _insert_document_type(migrated_engine, organization_id, "legacy", "labour")

    command.downgrade(config, "0013_compliance_documents")
    assert _safety_domain(migrated_engine, labour_type) == "labour"
    assert _safety_domain(migrated_engine, fire_type) == "fire"
    with pytest.raises(IntegrityError, match="ck_document_types_safety_domain"):
        _insert_document_type(
            migrated_engine, organization_id, "too_new", "transport_security"
        )

    command.upgrade(config, "head")
    assert _safety_domain(migrated_engine, labour_type) == "transport_security"

from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Engine, inspect

from alembic import command

pytest_plugins = ("tests.infrastructure.db_fixtures",)

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions" / "0015_document_shelf.py"
)
_TABLES = {"shelf_sections", "shelf_subsections", "shelf_slots", "shelf_slot_documents"}


def test_0015_document_shelf_migration_module() -> None:
    spec = util.spec_from_file_location("migration_0015", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0015_document_shelf"
    assert migration.down_revision == "0014_transport_security_domain"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


@pytest.mark.db
def test_0015_schema(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    assert _TABLES.issubset(set(inspector.get_table_names()))

    def uniques(table: str) -> set[str]:
        return {item["name"] for item in inspector.get_unique_constraints(table)}

    def checks(table: str) -> set[str]:
        return {item["name"] for item in inspector.get_check_constraints(table)}

    def fks(table: str) -> dict[tuple[str, ...], str]:
        return {
            tuple(fk["constrained_columns"]): fk["options"]["ondelete"].upper()
            for fk in inspector.get_foreign_keys(table)
        }

    assert {
        "uq_shelf_sections_organization_id_code",
        "uq_shelf_sections_organization_id_number",
    } <= uniques("shelf_sections")
    assert {
        "ck_shelf_sections_safety_domain",
        "ck_shelf_sections_number_range",
        "ck_shelf_sections_version_positive",
    } <= checks("shelf_sections")

    assert {
        "uq_shelf_subsections_organization_id_code",
        "uq_shelf_subsections_section_id_position",
    } <= uniques("shelf_subsections")
    assert fks("shelf_subsections")[("section_id",)] == "RESTRICT"

    assert "uq_shelf_slots_organization_id_code" in uniques("shelf_slots")
    assert {
        "ck_shelf_slots_kept_on",
        "ck_shelf_slots_obligation_level",
        "ck_shelf_slots_curated_status",
        "ck_shelf_slots_basis_confidence",
        "ck_shelf_slots_exclusion_reason",
        "ck_shelf_slots_exclusion_status_before",
        "ck_shelf_slots_exclusion_complete",
        "ck_shelf_slots_exclusion_comment_length",
        "ck_shelf_slots_condition_required",
        "ck_shelf_slots_title_length",
        "ck_shelf_slots_short_title_nonempty",
        "ck_shelf_slots_review_period_positive",
        "ck_shelf_slots_version_positive",
    } <= checks("shelf_slots")
    slot_fks = fks("shelf_slots")
    assert slot_fks[("organization_id",)] == "CASCADE"
    assert slot_fks[("section_id",)] == "RESTRICT"
    assert slot_fks[("subsection_id",)] == "RESTRICT"
    for column in ("created_by", "updated_by", "excluded_by"):
        assert slot_fks[(column,)] == "RESTRICT", column
    assert {
        "ix_shelf_slots_organization_id_section_id",
        "ix_shelf_slots_organization_id_subsection_id",
    } <= {item["name"] for item in inspector.get_indexes("shelf_slots")}

    link_pk = inspector.get_pk_constraint("shelf_slot_documents")
    assert link_pk["constrained_columns"] == ["slot_id", "document_id"]
    link_fks = fks("shelf_slot_documents")
    assert link_fks[("slot_id",)] == "CASCADE"
    assert link_fks[("document_id",)] == "RESTRICT"
    assert "uq_shelf_slot_documents_slot_id_position" in uniques("shelf_slot_documents")
    assert "ix_shelf_slot_documents_organization_id_document_id" in {
        item["name"] for item in inspector.get_indexes("shelf_slot_documents")
    }


@pytest.mark.db
def test_0015_downgrade_removes_shelf_tables(database_url: str, migrated_engine: Engine) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.downgrade(config, "0014_transport_security_domain")
    tables = set(inspect(migrated_engine).get_table_names())
    assert not (_TABLES & tables)
    assert "compliance_documents" in tables

    command.upgrade(config, "head")
    assert _TABLES.issubset(set(inspect(migrated_engine).get_table_names()))

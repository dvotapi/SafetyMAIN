from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

pytest_plugins = ("tests.infrastructure.db_fixtures",)


_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "0013_compliance_documents.py"
)


def test_0013_compliance_documents_migration_module() -> None:
    spec = util.spec_from_file_location("migration_0013", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    migration = util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0013_compliance_documents"
    assert migration.down_revision == "0012_risk_controls"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


@pytest.mark.db
def test_0013_schema(migrated_engine) -> None:
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    assert {"document_types", "compliance_documents", "document_files"}.issubset(tables)

    # document_types columns
    dt_cols = {col["name"]: col for col in inspector.get_columns("document_types")}
    for name in (
        "id",
        "organization_id",
        "code",
        "title_ru",
        "safety_domain",
        "subject_kind",
        "review_period_months",
        "validity_months",
        "periodicity_months",
        "warning_thresholds_days",
        "requires_acknowledgement",
        "requires_approval_order",
        "legal_basis",
        "legal_basis_reference",
        "is_active",
        "created_at",
        "updated_at",
    ):
        assert name in dt_cols, f"document_types.{name} missing"
    assert str(dt_cols["warning_thresholds_days"]["type"]).upper().startswith("JSONB")
    assert "TIMESTAMP" in str(dt_cols["created_at"]["type"]).upper()

    dt_uniques = {u["name"] for u in inspector.get_unique_constraints("document_types")}
    assert "uq_document_types_organization_id_code" in dt_uniques
    dt_checks = {c["name"] for c in inspector.get_check_constraints("document_types")}
    assert {
        "ck_document_types_safety_domain",
        "ck_document_types_subject_kind",
        "ck_document_types_periods_positive",
        "ck_document_types_single_period",
        "ck_document_types_warning_thresholds",
    }.issubset(dt_checks)

    # compliance_documents columns
    cd_cols = {col["name"]: col for col in inspector.get_columns("compliance_documents")}
    for name in (
        "id",
        "organization_id",
        "document_type_id",
        "subject_kind",
        "subject_id",
        "code",
        "title",
        "status",
        "issued_at",
        "effective_from",
        "next_review_at",
        "approved_by_document_id",
        "supersedes_document_id",
        "superseded_by_document_id",
        "applicability",
        "source",
        "notes",
        "status_before_archive",
        "archive_reason",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "version",
    ):
        assert name in cd_cols, f"compliance_documents.{name} missing"
    for date_col in ("issued_at", "effective_from", "next_review_at"):
        assert str(cd_cols[date_col]["type"]).upper() == "DATE", date_col
    assert "TIMESTAMP" in str(cd_cols["created_at"]["type"]).upper()
    assert str(cd_cols["applicability"]["type"]).upper().startswith("JSONB")

    cd_checks = {c["name"] for c in inspector.get_check_constraints("compliance_documents")}
    assert {
        "ck_compliance_documents_status",
        "ck_compliance_documents_source",
        "ck_compliance_documents_subject_kind",
        "ck_compliance_documents_version_positive",
        "ck_compliance_documents_archive_details",
        "ck_compliance_documents_archive_reason_nonempty",
        "ck_compliance_documents_subject_id",
        "ck_compliance_documents_no_self_reference",
    }.issubset(cd_checks)

    cd_indexes = {ix["name"]: ix for ix in inspector.get_indexes("compliance_documents")}
    assert {
        "uq_compliance_documents_org_code_in_force",
        "ix_compliance_documents_organization_id_status",
        "ix_compliance_documents_organization_id_document_type_id",
        "ix_compliance_documents_organization_id_next_review_at",
    }.issubset(cd_indexes)
    partial = cd_indexes["uq_compliance_documents_org_code_in_force"]
    assert partial["unique"] is True
    where = (partial.get("dialect_options", {}) or {}).get("postgresql_where") or ""
    assert "active" in str(where) and "under_review" in str(where)

    # FK ondelete
    cd_fks = {tuple(fk["constrained_columns"]): fk for fk in inspector.get_foreign_keys("compliance_documents")}
    assert cd_fks[("organization_id",)]["options"]["ondelete"].upper() == "CASCADE"
    assert cd_fks[("document_type_id",)]["options"]["ondelete"].upper() == "RESTRICT"
    assert cd_fks[("created_by",)]["options"]["ondelete"].upper() == "RESTRICT"
    assert cd_fks[("updated_by",)]["options"]["ondelete"].upper() == "RESTRICT"
    for col in ("approved_by_document_id", "supersedes_document_id", "superseded_by_document_id"):
        assert cd_fks[(col,)]["options"]["ondelete"].upper() == "SET NULL", col

    # document_files
    df_cols = {col["name"]: col for col in inspector.get_columns("document_files")}
    for name in (
        "id",
        "document_id",
        "position",
        "bucket",
        "key",
        "size_bytes",
        "content_type",
        "sha256",
        "original_filename",
        "uploaded_at",
        "uploaded_by",
    ):
        assert name in df_cols, f"document_files.{name} missing"

    df_uniques = {u["name"] for u in inspector.get_unique_constraints("document_files")}
    assert {
        "uq_document_files_document_id_position",
        "uq_document_files_document_id_key",
    }.issubset(df_uniques)
    df_checks = {c["name"] for c in inspector.get_check_constraints("document_files")}
    assert {
        "ck_document_files_position_nonnegative",
        "ck_document_files_size_positive",
        "ck_document_files_sha256_hex",
    }.issubset(df_checks)

    df_fks = {tuple(fk["constrained_columns"]): fk for fk in inspector.get_foreign_keys("document_files")}
    assert df_fks[("document_id",)]["options"]["ondelete"].upper() == "CASCADE"
    assert df_fks[("uploaded_by",)]["options"]["ondelete"].upper() == "RESTRICT"

    with migrated_engine.connect() as connection:
        head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert head == ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()


@pytest.mark.db
def test_0013_downgrade_removes_tables(database_url: str, migrated_engine) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.downgrade(config, "0012_risk_controls")
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    assert "compliance_documents" not in tables
    assert "document_files" not in tables
    assert "document_types" not in tables
    assert "risk_controls" in tables  # earlier table preserved

    command.upgrade(config, "head")
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    assert {"document_types", "compliance_documents", "document_files"}.issubset(tables)

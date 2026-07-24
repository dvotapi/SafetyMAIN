from __future__ import annotations

import ast
from pathlib import Path

from backend.bootstrap.container import create_container
from backend.bootstrap.security_validation import SecurityConfigurationError
from backend.bootstrap.settings import AppSettings
from backend.core.infrastructure.persistence.in_memory.unit_of_work import (
    InMemoryUnitOfWork,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from tests.architecture.architecture_imports import assert_no_forbidden_imports

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
API_ROOT = BACKEND_ROOT / "api"
APPLICATION_ROOT = BACKEND_ROOT / "core" / "application"
DOMAIN_ROOT = BACKEND_ROOT / "core" / "domain"
REFRESH_MODEL = (
    "backend.core.infrastructure.persistence.sqlalchemy.models."
    "refresh_token_session_model"
)
REFRESH_REPO_PATH = (
    BACKEND_ROOT
    / "core"
    / "infrastructure"
    / "persistence"
    / "sqlalchemy"
    / "repositories"
    / "refresh_token_session_repository.py"
)
REFRESH_MODEL_PATH = (
    BACKEND_ROOT
    / "core"
    / "infrastructure"
    / "persistence"
    / "sqlalchemy"
    / "models"
    / "refresh_token_session_model.py"
)


def test_api_modules_do_not_import_refresh_session_sqlalchemy_model() -> None:
    assert_no_forbidden_imports(
        API_ROOT,
        forbidden_prefixes=(REFRESH_MODEL,),
        rule="API must not import refresh-session SQLAlchemy models.",
    )


def test_handlers_do_not_import_refresh_session_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        APPLICATION_ROOT / "handlers",
        forbidden_prefixes=(
            REFRESH_MODEL,
            "sqlalchemy",
        ),
        rule="Handlers must use the refresh-session repository contract.",
    )


def test_domain_value_objects_do_not_import_fastapi_or_sqlalchemy() -> None:
    source = (DOMAIN_ROOT / "value_objects" / "refresh_session.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    for module in imported:
        assert not module.startswith("fastapi")
        assert not module.startswith("sqlalchemy")


def test_refresh_session_repository_does_not_commit() -> None:
    source = REFRESH_REPO_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "commit"
        ):
            raise AssertionError(
                "SQLAlchemyRefreshTokenSessionRepository must not commit."
            )


def test_refresh_token_session_model_has_no_raw_token_columns() -> None:
    source = REFRESH_MODEL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    column_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            column_names.add(node.target.id)
    forbidden = {
        "access_token",
        "refresh_token",
        "authorization",
        "authorization_header",
        "raw_jti",
        "jti",
        "token_payload",
        "jwt",
    }
    overlap = column_names & forbidden
    assert not overlap, f"Forbidden raw token columns: {sorted(overlap)}"


def test_container_with_database_url_uses_sqlalchemy_refresh_uow(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url="postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain",
        cors_allowed_origins=(),
        jwt_secret_key="guardrail-test-secret-key-32chars!!",
        jwt_issuer="safetymain-test",
        refresh_token_rotation_enabled=True,
    )
    container = create_container(settings)
    try:
        uow = container.uow_factory()
        assert isinstance(uow, SQLAlchemyUnitOfWork)
        assert not isinstance(uow, InMemoryUnitOfWork)
    finally:
        container.dispose()


def test_production_requires_postgres_for_refresh_sessions() -> None:
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="production",
        database_url=None,
        cors_allowed_origins=(),
        jwt_secret_key="production-guardrail-secret-key-32b",
        jwt_issuer="safetymain-production",
        auth_enforcement=True,
        refresh_token_rotation_enabled=True,
    )
    try:
        create_container(settings)
        raise AssertionError("expected SecurityConfigurationError")
    except SecurityConfigurationError as error:
        assert "database_url" in str(error).lower()


def test_create_container_source_rejects_production_memory_refresh() -> None:
    source = (BACKEND_ROOT / "bootstrap" / "container.py").read_text(encoding="utf-8")
    assert "Production refresh sessions require PostgreSQL persistence." in source
    assert "shared_refresh_sessions" in source


def test_in_memory_refresh_repository_is_not_imported_by_api_routers() -> None:
    assert_no_forbidden_imports(
        API_ROOT / "routers",
        forbidden_prefixes=(
            "backend.core.infrastructure.persistence.in_memory.refresh_token_session_repository",
            "backend.core.infrastructure.persistence.sqlalchemy.repositories.refresh_token_session_repository",
        ),
        rule="Routes must not construct refresh-session repositories.",
    )

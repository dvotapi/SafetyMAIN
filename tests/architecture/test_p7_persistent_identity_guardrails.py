from __future__ import annotations

import ast
from pathlib import Path

from backend.bootstrap.container import create_container
from backend.bootstrap.security_validation import SecurityConfigurationError
from backend.bootstrap.settings import AppSettings
from backend.core.infrastructure.auth.in_memory_identity_store import (
    InMemoryIdentityStore,
)
from backend.core.infrastructure.auth.in_memory_membership_store import (
    InMemoryMembershipStore,
)
from backend.core.infrastructure.auth.sqlalchemy_identity_adapter import (
    SQLAlchemyIdentityAdapter,
)
from backend.core.infrastructure.auth.sqlalchemy_membership_adapter import (
    SQLAlchemyMembershipAdapter,
)
from tests.architecture.architecture_imports import assert_no_forbidden_imports

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
API_ROOT = BACKEND_ROOT / "api"
APPLICATION_ROOT = BACKEND_ROOT / "core" / "application"
DOMAIN_ROOT = BACKEND_ROOT / "core" / "domain"
REPOSITORIES_ROOT = (
    BACKEND_ROOT / "core" / "infrastructure" / "persistence" / "sqlalchemy" / "repositories"
)


def test_api_modules_do_not_import_identity_sqlalchemy_models() -> None:
    assert_no_forbidden_imports(
        API_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure.persistence.sqlalchemy.models.user_model",
            "backend.core.infrastructure.persistence.sqlalchemy.models.organization_model",
            "backend.core.infrastructure.persistence.sqlalchemy.models.membership_model",
        ),
        rule="API must not import identity SQLAlchemy models.",
    )


def test_domain_modules_do_not_import_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        DOMAIN_ROOT,
        forbidden_prefixes=("sqlalchemy",),
        rule="Domain must not import SQLAlchemy.",
    )


def test_handlers_do_not_import_sqlalchemy_identity_models() -> None:
    assert_no_forbidden_imports(
        APPLICATION_ROOT / "handlers",
        forbidden_prefixes=(
            "backend.core.infrastructure.persistence.sqlalchemy.models",
            "sqlalchemy",
        ),
        rule="Handlers must depend on repository contracts, not ORM models.",
    )


def test_identity_repositories_do_not_commit() -> None:
    for path in REPOSITORIES_ROOT.glob("*user*repository.py"):
        _assert_no_commit_call(path)
    for path in REPOSITORIES_ROOT.glob("*organization*repository.py"):
        _assert_no_commit_call(path)
    for path in REPOSITORIES_ROOT.glob("*membership*repository.py"):
        _assert_no_commit_call(path)


def test_container_with_database_url_uses_sqlalchemy_adapters(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url="postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain",
        cors_allowed_origins=(),
        jwt_secret_key="guardrail-test-secret-key-32chars!!",
        jwt_issuer="safetymain-test",
    )
    container = create_container(settings)
    try:
        assert isinstance(container.identity_store, SQLAlchemyIdentityAdapter)
        assert isinstance(container.membership_store, SQLAlchemyMembershipAdapter)
        assert not isinstance(container.identity_store, InMemoryIdentityStore)
        assert not isinstance(container.membership_store, InMemoryMembershipStore)
    finally:
        container.dispose()


def test_production_rejects_in_memory_identity_injection() -> None:
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="production",
        database_url="postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain",
        cors_allowed_origins=(),
        jwt_secret_key="production-guardrail-secret-key-32b",
        jwt_issuer="safetymain-production",
        auth_enforcement=True,
    )
    try:
        create_container(settings, identity_store=InMemoryIdentityStore())
        raise AssertionError("expected SecurityConfigurationError")
    except SecurityConfigurationError as error:
        assert "in-memory" in str(error).lower()


def test_create_container_source_has_no_silent_production_memory_fallback() -> None:
    source = (BACKEND_ROOT / "bootstrap" / "container.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    # Production branches must raise rather than construct InMemory* stores.
    assert "Production must not use in-memory identity or membership stores." in source
    assert "Production identity lookup requires SQLAlchemy persistence." in source
    assert isinstance(tree, ast.Module)


def _assert_no_commit_call(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != "commit", f"{path.name} must not call commit()"

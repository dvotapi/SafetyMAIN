from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import (
    assert_no_forbidden_imports,
    assert_no_forbidden_method_calls,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_ROUTERS_ROOT = PROJECT_ROOT / "backend" / "api" / "routers"
API_SCHEMAS_ROOT = PROJECT_ROOT / "backend" / "api" / "schemas"
API_MAPPERS_ROOT = PROJECT_ROOT / "backend" / "api" / "mappers"
API_PARAMS_ROOT = PROJECT_ROOT / "backend" / "api" / "params"
KNOWLEDGE_OBJECTS_ROUTER = API_ROUTERS_ROOT / "knowledge_objects.py"
RELATIONS_ROUTER = API_ROUTERS_ROOT / "relations.py"


def test_api_routers_do_not_import_sqlalchemy_orm_models() -> None:
    assert_no_forbidden_imports(
        API_ROUTERS_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure.persistence.sqlalchemy.models",
            "backend.core.infrastructure.persistence.sqlalchemy.repositories",
            "backend.core.infrastructure.persistence.sqlalchemy.unit_of_work",
        ),
        rule=(
            "API routers must depend on contracts/factories, not SQLAlchemy ORM "
            "models or concrete persistence adapters. Composition root exceptions "
            "live under backend.bootstrap."
        ),
    )


def test_api_schemas_do_not_import_domain_infrastructure() -> None:
    assert_no_forbidden_imports(
        API_SCHEMAS_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure",
            "sqlalchemy",
        ),
        rule="API schemas must remain transport-only and infrastructure-free.",
    )


def test_api_mappers_do_not_import_infrastructure() -> None:
    assert_no_forbidden_imports(
        API_MAPPERS_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure",
            "sqlalchemy",
        ),
        rule="API mappers must not depend on infrastructure adapters.",
    )


def test_knowledge_object_router_does_not_import_repositories() -> None:
    assert_no_forbidden_imports(
        KNOWLEDGE_OBJECTS_ROUTER.parent,
        forbidden_prefixes=(
            "backend.core.domain.repositories",
        ),
        rule=(
            "Knowledge Object API router must use application handlers rather than "
            "repository contracts directly."
        ),
    )


def test_relation_router_does_not_import_repositories() -> None:
    assert_no_forbidden_imports(
        RELATIONS_ROUTER.parent,
        forbidden_prefixes=(
            "backend.core.domain.repositories",
        ),
        rule=(
            "Relation API router must use application handlers rather than "
            "repository contracts directly."
        ),
    )


def test_search_params_do_not_import_infrastructure() -> None:
    assert_no_forbidden_imports(
        API_PARAMS_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure",
            "sqlalchemy",
        ),
        rule="Search parameter parsers must remain transport-only and infrastructure-free.",
    )


def test_api_routers_do_not_call_commit_or_rollback() -> None:
    assert_no_forbidden_method_calls(
        API_ROUTERS_ROOT,
        forbidden_methods=("commit", "rollback"),
        rule="API routers must not own transaction boundaries.",
    )

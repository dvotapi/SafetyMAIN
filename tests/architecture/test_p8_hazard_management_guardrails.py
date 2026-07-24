from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"
API_ROUTERS = PROJECT_ROOT / "backend" / "api" / "routers"
HAZARD_REPO = (
    PROJECT_ROOT
    / "backend"
    / "core"
    / "infrastructure"
    / "persistence"
    / "sqlalchemy"
    / "repositories"
    / "hazard_repository.py"
)
HAZARD_ROUTER = API_ROUTERS / "hazards.py"
HAZARD_HANDLERS = (
    APPLICATION_ROOT / "handlers" / "create_hazard.py",
    APPLICATION_ROOT / "handlers" / "update_hazard.py",
    APPLICATION_ROOT / "handlers" / "hazard_lifecycle.py",
    APPLICATION_ROOT / "handlers" / "get_list_hazards.py",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_hazard_domain_does_not_import_fastapi_or_sqlalchemy() -> None:
    for path in (
        DOMAIN_ROOT / "entities" / "hazard.py",
        DOMAIN_ROOT / "repositories" / "hazard_repository.py",
        DOMAIN_ROOT / "exceptions" / "hazard.py",
        DOMAIN_ROOT / "value_objects" / "hazard_code.py",
        DOMAIN_ROOT / "value_objects" / "hazard_query.py",
        DOMAIN_ROOT / "events" / "safety_events.py",
    ):
        imports = _imports(path)
        for name in imports:
            assert "fastapi" not in name
            assert "sqlalchemy" not in name
            assert not name.startswith("backend.api")
            assert not name.startswith("backend.core.infrastructure")


def test_hazard_handlers_do_not_import_orm_models() -> None:
    for path in HAZARD_HANDLERS:
        imports = _imports(path)
        for name in imports:
            assert "sqlalchemy" not in name
            assert "models" not in name or "domain" in name


def test_hazard_router_does_not_use_orm_sessions_or_delete() -> None:
    imports = _imports(HAZARD_ROUTER)
    source = HAZARD_ROUTER.read_text(encoding="utf-8")
    assert "sqlalchemy" not in " ".join(imports)
    assert "Session" not in source
    assert "@router.delete" not in source
    assert "handler.handle" in source


def test_create_hazard_request_rejects_client_organization_ownership() -> None:
    schema = (
        PROJECT_ROOT / "backend" / "api" / "schemas" / "hazards.py"
    ).read_text(encoding="utf-8")
    assert "class CreateHazardRequest" in schema
    create_block = schema.split("class CreateHazardRequest")[1].split("class ")[0]
    assert "organization_id" not in create_block


def test_hazard_repository_does_not_commit() -> None:
    source = HAZARD_REPO.read_text(encoding="utf-8")
    assert ".commit(" not in source


def test_hazard_repository_get_is_organization_scoped() -> None:
    source = (
        DOMAIN_ROOT / "repositories" / "hazard_repository.py"
    ).read_text(encoding="utf-8")
    assert "organization_id: OrganizationId" in source
    assert "def get(\n        self,\n        organization_id" in source or (
        "def get(" in source and "organization_id" in source
    )


def test_p8_002_documents_exist() -> None:
    required = (
        PROJECT_ROOT / "docs" / "domain" / "HazardManagement.md",
        PROJECT_ROOT / "docs" / "architecture" / "HazardPersistence.md",
        PROJECT_ROOT / "docs" / "architecture" / "SafetyAuthorization.md",
        PROJECT_ROOT / "docs" / "architecture" / "AuditTaxonomy.md",
        PROJECT_ROOT / "docs" / "api" / "HazardsAPI.md",
        PROJECT_ROOT / "docs" / "tasks" / "TASK-P8-002.md",
    )
    for path in required:
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").strip().startswith("#")

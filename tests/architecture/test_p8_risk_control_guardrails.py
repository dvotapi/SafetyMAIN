from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"
API_ROUTERS = PROJECT_ROOT / "backend" / "api" / "routers"


def _imports(path: Path) -> set[str]:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_risk_control_domain_is_infrastructure_free() -> None:
    for path in (
        DOMAIN_ROOT / "entities" / "risk_control.py",
        DOMAIN_ROOT / "repositories" / "risk_control_repository.py",
        DOMAIN_ROOT / "exceptions" / "risk_control.py",
        DOMAIN_ROOT / "value_objects" / "risk_control_components.py",
        DOMAIN_ROOT / "value_objects" / "risk_control_query.py",
        DOMAIN_ROOT / "value_objects" / "risk_control_code.py",
    ):
        imports = _imports(path)
        for name in imports:
            assert "fastapi" not in name
            assert "sqlalchemy" not in name
            assert not name.startswith("backend.api")
            assert not name.startswith("backend.core.infrastructure")


def test_risk_control_handlers_avoid_orm_and_future_bc() -> None:
    for path in (
        APPLICATION_ROOT / "handlers" / "create_risk_control.py",
        APPLICATION_ROOT / "handlers" / "get_list_risk_controls.py",
        APPLICATION_ROOT / "handlers" / "risk_control_lifecycle.py",
        APPLICATION_ROOT / "handlers" / "materialize_risk_controls.py",
    ):
        imports = _imports(path)
        for name in imports:
            assert "sqlalchemy" not in name
            assert "fastapi" not in name
            assert "inspection" not in name.split(".")[-1] or "Inspection" not in name
        text = path.read_text(encoding="utf-8")
        assert "IncidentRepository" not in text
        assert "TrainingRepository" not in text
        assert "CorrectiveActionRepository" not in text


def test_risk_control_router_has_no_delete_and_delegates() -> None:
    source = (API_ROUTERS / "risk_controls.py").read_text(encoding="utf-8")
    assert "@router.delete" not in source
    assert "handler.handle" in source
    assert "materialize" in source


def test_materialize_handler_does_not_save_assessment() -> None:
    source = (
        APPLICATION_ROOT / "handlers" / "materialize_risk_controls.py"
    ).read_text(encoding="utf-8")
    assert "risk_assessments.save" not in source
    assert "risk_controls.add" in source


def test_risk_control_repository_does_not_commit() -> None:
    source = (
        PROJECT_ROOT
        / "backend"
        / "core"
        / "infrastructure"
        / "persistence"
        / "sqlalchemy"
        / "repositories"
        / "risk_control_repository.py"
    ).read_text(encoding="utf-8")
    assert ".commit(" not in source


def test_p8_004_documents_exist() -> None:
    required = (
        PROJECT_ROOT / "docs" / "domain" / "RiskControl.md",
        PROJECT_ROOT / "docs" / "architecture" / "RiskControlPersistence.md",
        PROJECT_ROOT / "docs" / "api" / "RiskControlsAPI.md",
        PROJECT_ROOT / "docs" / "tasks" / "TASK-P8-004.md",
        PROJECT_ROOT / "docs" / "tasks" / "TASK-P8-004-H1.md",
    )
    for path in required:
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").strip().startswith("#")

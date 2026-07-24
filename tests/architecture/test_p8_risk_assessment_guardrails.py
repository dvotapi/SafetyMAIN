from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"
API_ROUTERS = PROJECT_ROOT / "backend" / "api" / "routers"


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


def test_risk_assessment_domain_is_infrastructure_free() -> None:
    for path in (
        DOMAIN_ROOT / "entities" / "risk_assessment.py",
        DOMAIN_ROOT / "repositories" / "risk_assessment_repository.py",
        DOMAIN_ROOT / "exceptions" / "risk_assessment.py",
        DOMAIN_ROOT / "services" / "assessment_profiles.py",
        DOMAIN_ROOT / "value_objects" / "risk_assessment_components.py",
    ):
        imports = _imports(path)
        for name in imports:
            assert "fastapi" not in name
            assert "sqlalchemy" not in name
            assert not name.startswith("backend.api")
            assert not name.startswith("backend.core.infrastructure")


def test_risk_assessment_handlers_avoid_orm() -> None:
    for path in (
        APPLICATION_ROOT / "handlers" / "create_risk_assessment.py",
        APPLICATION_ROOT / "handlers" / "update_risk_assessment.py",
        APPLICATION_ROOT / "handlers" / "risk_assessment_lifecycle.py",
        APPLICATION_ROOT / "handlers" / "get_list_risk_assessments.py",
    ):
        imports = _imports(path)
        for name in imports:
            assert "sqlalchemy" not in name


def test_risk_assessment_router_has_no_delete() -> None:
    source = (API_ROUTERS / "risk_assessments.py").read_text(encoding="utf-8")
    assert "@router.delete" not in source
    assert "handler.handle" in source


def test_risk_assessment_repository_does_not_commit() -> None:
    source = (
        PROJECT_ROOT
        / "backend"
        / "core"
        / "infrastructure"
        / "persistence"
        / "sqlalchemy"
        / "repositories"
        / "risk_assessment_repository.py"
    ).read_text(encoding="utf-8")
    assert ".commit(" not in source


def test_p8_003_documents_exist() -> None:
    required = (
        PROJECT_ROOT / "docs" / "domain" / "RiskAssessment.md",
        PROJECT_ROOT / "docs" / "architecture" / "RiskAssessmentPersistence.md",
        PROJECT_ROOT / "docs" / "api" / "RiskAssessmentsAPI.md",
        PROJECT_ROOT / "docs" / "tasks" / "TASK-P8-003.md",
    )
    for path in required:
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").strip().startswith("#")

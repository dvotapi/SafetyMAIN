from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.architecture_imports import (
    extract_imports,
    find_forbidden_imports,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
DOCS_DOMAIN = PROJECT_ROOT / "docs" / "domain"

SAFETY_PYTHON_FILES = (
    DOMAIN_ROOT / "entities" / "hazard.py",
    DOMAIN_ROOT / "entities" / "risk.py",
    DOMAIN_ROOT / "entities" / "inspection.py",
    DOMAIN_ROOT / "entities" / "incident.py",
    DOMAIN_ROOT / "entities" / "corrective_action.py",
    DOMAIN_ROOT / "entities" / "training_permit_emergency_asset.py",
    DOMAIN_ROOT / "value_objects" / "safety_ids.py",
    DOMAIN_ROOT / "value_objects" / "safety_enums.py",
    DOMAIN_ROOT / "value_objects" / "hierarchy_of_controls.py",
    DOMAIN_ROOT / "events" / "safety_events.py",
    DOMAIN_ROOT / "services" / "safety_lifecycle.py",
    DOMAIN_ROOT / "exceptions" / "safety.py",
    DOMAIN_ROOT / "repositories" / "hazard_repository.py",
    DOMAIN_ROOT / "repositories" / "risk_repository.py",
    DOMAIN_ROOT / "repositories" / "inspection_repository.py",
    DOMAIN_ROOT / "repositories" / "incident_repository.py",
    DOMAIN_ROOT / "repositories" / "corrective_action_repository.py",
    DOMAIN_ROOT / "repositories" / "safety_supporting_repositories.py",
)

REQUIRED_DOCS = (
    "SafetyDomainFoundation.md",
    "UbiquitousLanguage.md",
    "Aggregates.md",
    "DomainEvents.md",
    "LifecycleRules.md",
)

FORBIDDEN_PREFIXES = (
    "backend.core.application",
    "backend.core.infrastructure",
    "backend.api",
    "backend.bootstrap",
    "fastapi",
    "sqlalchemy",
)


def test_safety_foundation_documents_exist() -> None:
    for name in REQUIRED_DOCS:
        path = DOCS_DOMAIN / name
        assert path.is_file(), f"Missing Safety foundation document: {name}"
        text = path.read_text(encoding="utf-8")
        assert "TASK-P8-001" in text
        assert text.strip().startswith("#")


def test_safety_domain_modules_do_not_import_infrastructure_or_api() -> None:
    for path in SAFETY_PYTHON_FILES:
        assert path.is_file(), path
        for imported in extract_imports(path):
            for prefix in FORBIDDEN_PREFIXES:
                assert not (
                    imported == prefix or imported.startswith(f"{prefix}.")
                ), f"{path} imports forbidden module {imported}"


def test_domain_layer_still_forbids_outer_dependencies_including_safety() -> None:
    violations = find_forbidden_imports(
        DOMAIN_ROOT,
        forbidden_prefixes=FORBIDDEN_PREFIXES,
        rule="Domain layer must not depend on outer layers.",
    )
    assert violations == ()


def test_safety_repository_contracts_are_protocols_without_sqlalchemy() -> None:
    repo_files = [
        path for path in SAFETY_PYTHON_FILES if "repositories" in path.parts
    ]
    for path in repo_files:
        source = path.read_text(encoding="utf-8")
        assert "Protocol" in source
        assert "sqlalchemy" not in source.lower()
        tree = ast.parse(source)
        assert any(isinstance(node, ast.ClassDef) for node in tree.body)


def test_safety_entities_do_not_reference_api_schemas() -> None:
    for path in SAFETY_PYTHON_FILES:
        if "entities" not in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        assert "backend.api" not in source


def test_aggregates_doc_forbids_circular_ownership() -> None:
    text = (DOCS_DOMAIN / "Aggregates.md").read_text(encoding="utf-8")
    assert "circular" in text.lower()
    assert "Hazard" in text and "Risk" in text and "Inspection" in text

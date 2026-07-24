from __future__ import annotations

import ast
import re
from pathlib import Path

from backend.core.domain.security_events import security_event_types
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_chain_head import (
    organization_advisory_lock_key_text,
)
from tests.architecture.architecture_imports import (
    assert_no_forbidden_imports,
    extract_imports,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
APPLICATION_ROOT = BACKEND_ROOT / "core" / "application"
DOMAIN_SERVICES = BACKEND_ROOT / "core" / "domain" / "services"
API_ROOT = BACKEND_ROOT / "api"
HANDLERS_ROOT = APPLICATION_ROOT / "handlers"
AUDIT_APPLICATION_ROOT = APPLICATION_ROOT / "audit"


def test_domain_integrity_modules_do_not_import_fastapi_or_sqlalchemy() -> None:
    forbidden = ("fastapi", "starlette", "sqlalchemy", "backend.api")
    for relative in (
        "audit_event_canonicalizer.py",
        "audit_integrity_service.py",
    ):
        path = DOMAIN_SERVICES / relative
        for imported in extract_imports(path):
            assert not any(
                imported == prefix or imported.startswith(f"{prefix}.")
                for prefix in forbidden
            ), f"{path.name} imports {imported}"


def test_api_modules_do_not_import_audit_sqlalchemy_models() -> None:
    assert_no_forbidden_imports(
        API_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model",
        ),
        rule="API must not import audit SQLAlchemy models.",
    )


def test_handlers_do_not_touch_chain_heads_or_hashing() -> None:
    for path in HANDLERS_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "AuditChainHeadModel" not in source
        assert "pg_advisory_xact_lock" not in source
        assert "hashlib.sha256" not in source
        assert "compute_integrity_hash" not in source


def test_recorders_do_not_calculate_integrity_hashes() -> None:
    for path in AUDIT_APPLICATION_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "hashlib" not in source
        assert "finalize_event" not in source
        assert "AuditChainHeadModel" not in source
        assert "pg_advisory_xact_lock" not in source


def test_production_audit_event_construction_is_limited_to_recorders() -> None:
    allowed = {
        (AUDIT_APPLICATION_ROOT / "administrative_audit_recorder.py").resolve(),
        (AUDIT_APPLICATION_ROOT / "authentication_security_event_recorder.py").resolve(),
        (
            BACKEND_ROOT
            / "core"
            / "infrastructure"
            / "persistence"
            / "sqlalchemy"
            / "mappers"
            / "audit_event_mapper.py"
        ).resolve(),
        (BACKEND_ROOT / "core" / "domain" / "entities" / "audit_event.py").resolve(),
    }
    pattern = re.compile(r"\bAuditEvent\s*\(")
    offenders: list[str] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        if path.resolve() in allowed:
            continue
        if "migrations" in path.parts or "alembic" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == [], f"Unexpected AuditEvent(...) construction: {offenders}"


def test_audit_action_values_are_registered_in_taxonomy() -> None:
    registered = security_event_types()
    missing = sorted(
        action.value for action in AuditAction if action.value not in registered
    )
    assert missing == [], f"AuditAction values missing from taxonomy: {missing}"


def test_known_security_event_name_literals_are_centralized() -> None:
    """Production modules outside taxonomy/AuditAction must not redefine event names."""

    allowed_dirs = {
        BACKEND_ROOT / "core" / "domain" / "security_events",
        BACKEND_ROOT / "core" / "domain" / "value_objects",
    }
    pattern = re.compile(
        r'"(authentication\.(?:login|refresh)\.(?:succeeded|failed)|'
        r'authorization\.permission_denied)"'
    )
    offenders: list[str] = []
    for path in BACKEND_ROOT.rglob("*.py"):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        if any(allowed in path.parents or path.parent == allowed for allowed in allowed_dirs):
            continue
        if path.name == "audit_action.py":
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert offenders == [], f"Duplicated security-event name literals: {offenders}"


def test_advisory_lock_key_derivation_is_stable_and_not_python_hash() -> None:
    organization_id = OrganizationId(
        value=__import__("uuid").UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    )
    assert (
        organization_advisory_lock_key_text(organization_id)
        == "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    )
    # Guard against accidental use of randomized hash() in repository source.
    repository = (
        BACKEND_ROOT
        / "core"
        / "infrastructure"
        / "persistence"
        / "sqlalchemy"
        / "repositories"
        / "audit_event_repository.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(repository)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash"
    assert "organization_advisory_lock_key_text" in repository
    assert "pg_advisory_xact_lock(hashtext(" in repository

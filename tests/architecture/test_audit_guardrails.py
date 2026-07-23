from __future__ import annotations

import inspect
from pathlib import Path

from backend.core.application.authorization.policies.resource_permissions import AUDIT_READ
from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.domain.value_objects.permission import SystemPermission
from tests.architecture.architecture_imports import (
    assert_at_most_one_require_permission_per_route_handler,
    assert_no_forbidden_imports,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_AUDIT_ROOT = PROJECT_ROOT / "backend" / "core" / "application" / "audit"
API_DEPENDENCIES = PROJECT_ROOT / "backend" / "api" / "dependencies.py"
API_EXCEPTION_HANDLERS = PROJECT_ROOT / "backend" / "api" / "exception_handlers.py"
API_ROUTERS_ROOT = PROJECT_ROOT / "backend" / "api" / "routers"
AUDIT_ROUTER = API_ROUTERS_ROOT / "admin_audit_events.py"


def test_application_audit_modules_do_not_import_fastapi() -> None:
    assert_no_forbidden_imports(
        APPLICATION_AUDIT_ROOT,
        forbidden_prefixes=("fastapi", "starlette"),
        rule="Application audit modules must remain framework-independent.",
    )


def test_audit_router_does_not_construct_audit_events_directly() -> None:
    source = AUDIT_ROUTER.read_text(encoding="utf-8")
    assert "AuditEvent(" not in source
    assert "AuditRecordSpec(" not in source


def test_audit_repository_contract_is_append_only() -> None:
    public_methods = {
        name
        for name, _ in inspect.getmembers(
            AuditEventRepositoryContract,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    }

    assert public_methods == {"add", "get", "list_events"}


def test_audit_read_permission_exists_without_audit_write() -> None:
    assert AUDIT_READ.value == "audit:read"
    assert not hasattr(SystemPermission, "AUDIT_WRITE")


def test_permission_denial_auditing_is_centralized_in_require_permission() -> None:
    dependencies_source = API_DEPENDENCIES.read_text(encoding="utf-8")
    exception_handlers_source = API_EXCEPTION_HANDLERS.read_text(encoding="utf-8")

    assert "record_permission_denial" in dependencies_source
    assert "build_permission_denial_audit_spec" in dependencies_source
    assert "record_permission_denial" not in exception_handlers_source


def test_admin_routers_do_not_record_permission_denials_directly() -> None:
    for router_path in API_ROUTERS_ROOT.glob("admin_*.py"):
        source = router_path.read_text(encoding="utf-8")
        assert "record_permission_denial" not in source
        assert "AUTHORIZATION_PERMISSION_DENIED" not in source


def test_route_handlers_use_at_most_one_require_permission_dependency() -> None:
    assert_at_most_one_require_permission_per_route_handler(API_ROUTERS_ROOT)

from __future__ import annotations

from pathlib import Path

from backend.core.domain.security_events import (
    SECURITY_EVENT_REGISTRY,
    SecurityEventProducerOwner,
    security_event_descriptor_for,
    security_event_types,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from tests.architecture.architecture_imports import assert_no_forbidden_imports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECURITY_EVENTS_ROOT = PROJECT_ROOT / "backend" / "core" / "domain" / "security_events"
API_ROUTERS_ROOT = PROJECT_ROOT / "backend" / "api" / "routers"
API_DEPENDENCIES = PROJECT_ROOT / "backend" / "api" / "dependencies.py"
API_EXCEPTION_HANDLERS = PROJECT_ROOT / "backend" / "api" / "exception_handlers.py"


def test_security_event_taxonomy_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        SECURITY_EVENTS_ROOT,
        forbidden_prefixes=(
            "fastapi",
            "starlette",
            "sqlalchemy",
            "backend.core.infrastructure",
            "backend.core.application",
            "backend.api",
        ),
        rule="Security event taxonomy must remain a transport- and infrastructure-free domain module.",
    )


def test_every_audit_action_has_registered_security_event_descriptor() -> None:
    published_actions = {action.value for action in AuditAction}
    registered_types = security_event_types()

    missing = published_actions - registered_types
    extra = registered_types - published_actions

    assert not missing, f"Missing registry descriptors for: {sorted(missing)}"
    assert not extra, f"Unexpected registry descriptors without AuditAction: {sorted(extra)}"


def test_registry_has_unique_event_type_identifiers() -> None:
    event_types = [descriptor.event_type for descriptor in SECURITY_EVENT_REGISTRY]
    assert len(event_types) == len(set(event_types))


def test_every_descriptor_has_exactly_one_producer_owner() -> None:
    for descriptor in SECURITY_EVENT_REGISTRY:
        assert isinstance(descriptor.producer_owner, SecurityEventProducerOwner)


def test_authorization_permission_denied_producer_mapping() -> None:
    descriptor = security_event_descriptor_for("authorization.permission_denied")
    assert descriptor is not None
    assert descriptor.producer_owner is SecurityEventProducerOwner.AUTHORIZATION


def test_administrative_events_use_administrative_audit_producer() -> None:
    for action in AuditAction:
        if action is AuditAction.AUTHORIZATION_PERMISSION_DENIED:
            continue
        descriptor = security_event_descriptor_for(action.value)
        assert descriptor is not None
        assert descriptor.producer_owner is SecurityEventProducerOwner.ADMINISTRATIVE_AUDIT


def test_routers_do_not_define_security_event_registry_entries() -> None:
    for router_path in API_ROUTERS_ROOT.glob("*.py"):
        source = router_path.read_text(encoding="utf-8")
        assert "SecurityEventDescriptor(" not in source
        assert "SECURITY_EVENT_REGISTRY" not in source


def test_authorization_denial_production_remains_centralized() -> None:
    dependencies_source = API_DEPENDENCIES.read_text(encoding="utf-8")
    exception_handlers_source = API_EXCEPTION_HANDLERS.read_text(encoding="utf-8")

    assert "record_permission_denial" in dependencies_source
    assert "record_permission_denial" not in exception_handlers_source

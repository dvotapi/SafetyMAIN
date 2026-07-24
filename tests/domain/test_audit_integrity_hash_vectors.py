from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_integrity_service import AuditIntegrityService
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_integrity import AuditIntegrityHash
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _event(**overrides: object) -> AuditEvent:
    values: dict[str, object] = {
        "id": AuditEventId(value=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
        "actor_user_id": UserId(value=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")),
        "authorization_organization_id": OrganizationId(
            value=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
        ),
        "target_organization_id": None,
        "action": AuditAction.USER_CREATE,
        "resource_type": AuditResourceType.USER,
        "resource_id": UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
        "outcome": AuditOutcome.SUCCESS,
        "failure_code": None,
        "metadata": {"changed_fields": ["display_name"], "request_id": "req-1"},
        "occurred_at": datetime(2026, 7, 24, 14, 30, 0, 123456, tzinfo=UTC),
    }
    values.update(overrides)
    return AuditEvent(**values)  # type: ignore[arg-type]


def test_known_genesis_hash_vector() -> None:
    digest = AuditIntegrityService().compute_integrity_hash(_event(), previous_hash=None)
    assert digest.value == "4afd7661af4418fac01ba20d02d987df6bdbcb106af20c32d28f56112fd314a7"


def test_known_chained_hash_vector() -> None:
    previous = AuditIntegrityHash(
        value="4afd7661af4418fac01ba20d02d987df6bdbcb106af20c32d28f56112fd314a7"
    )
    digest = AuditIntegrityService().compute_integrity_hash(
        _event(id=AuditEventId(value=UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"))),
        previous_hash=previous,
    )
    assert digest.value == "79622b5d51f740731717bbbe4e38ab99503dc7c48da9f9539c81626449630794"


def test_known_empty_and_null_field_vectors() -> None:
    service = AuditIntegrityService()
    empty = service.compute_integrity_hash(_event(metadata={}), previous_hash=None)
    assert empty.value == "c70b9a1fe935d564338a1144e169a191c4f5f8cc0d88d74055c5539f985ea1f5"
    nullable = service.compute_integrity_hash(
        _event(resource_id=None, metadata={}),
        previous_hash=None,
    )
    assert nullable.value == "b3ca7af08646a5c331e87458935a0577c652aff6ad3c9ee00e92efd5cbc3a3b5"


def test_any_integrity_relevant_field_change_alters_hash() -> None:
    service = AuditIntegrityService()
    baseline = service.compute_integrity_hash(_event(), previous_hash=None)
    mutated = service.compute_integrity_hash(
        _event(metadata={"changed_fields": ["email"], "request_id": "req-1"}),
        previous_hash=None,
    )
    assert baseline != mutated

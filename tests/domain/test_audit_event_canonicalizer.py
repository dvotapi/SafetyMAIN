from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_event_canonicalizer import (
    AuditCanonicalizationError,
    build_canonical_audit_payload,
    canonical_audit_event_bytes,
    canonicalize_datetime,
    canonicalize_metadata,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_integrity import (
    CURRENT_AUDIT_INTEGRITY_VERSION,
)
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


def test_canonical_bytes_are_stable_across_key_order() -> None:
    left = _event(metadata={"request_id": "req-1", "changed_fields": ["a", "b"]})
    right = _event(metadata={"changed_fields": ["a", "b"], "request_id": "req-1"})
    assert canonical_audit_event_bytes(
        left, previous_integrity_hash=None
    ) == canonical_audit_event_bytes(right, previous_integrity_hash=None)


def test_nested_metadata_key_order_is_normalized() -> None:
    assert canonicalize_metadata({"z": 1, "a": {"y": 2, "x": 3}}) == {
        "a": {"x": 3, "y": 2},
        "z": 1,
    }


def test_uuid_and_datetime_normalization() -> None:
    payload = build_canonical_audit_payload(_event())
    assert payload["audit_event_id"] == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert payload["occurred_at"] == "2026-07-24T14:30:00.123456Z"
    assert payload["integrity_version"] == CURRENT_AUDIT_INTEGRITY_VERSION.value


def test_equivalent_timezone_offsets_canonicalize_identically() -> None:
    plus_two = timezone(timedelta(hours=2))
    left = datetime(2026, 7, 24, 16, 30, 0, tzinfo=plus_two)
    right = datetime(2026, 7, 24, 14, 30, 0, tzinfo=UTC)
    assert canonicalize_datetime(left) == canonicalize_datetime(right)


def test_canonical_payload_excludes_integrity_hashes() -> None:
    payload = build_canonical_audit_payload(_event())
    assert "integrity_hash" not in payload
    assert "previous_integrity_hash" not in payload
    assert "integrity_version" in payload


def test_canonical_bytes_include_explicit_null_previous_hash() -> None:
    encoded = canonical_audit_event_bytes(_event(), previous_integrity_hash=None)
    assert b'"previous_integrity_hash":null' in encoded


def test_unicode_and_empty_metadata() -> None:
    event = _event(metadata={"user_agent": "Кабинет ✓", "request_id": "r"})
    encoded = canonical_audit_event_bytes(event, previous_integrity_hash=None)
    assert "Кабинет ✓".encode() in encoded
    empty = canonical_audit_event_bytes(
        _event(metadata={}), previous_integrity_hash=None
    )
    assert b'"metadata":{}' in empty


def test_supported_scalar_metadata_types() -> None:
    assert canonicalize_metadata(
        {
            "request_id": "x",
            "changed_fields": [True, False, 1, 2.5, None, "s"],
        }
    ) == {
        "changed_fields": [True, False, 1, 2.5, None, "s"],
        "request_id": "x",
    }


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite_floats(value: float) -> None:
    with pytest.raises(AuditCanonicalizationError):
        canonicalize_metadata({"request_id": value})


def test_rejects_unsupported_metadata_objects() -> None:
    with pytest.raises(AuditCanonicalizationError):
        canonicalize_metadata({"request_id": {"nested", "set"}})
    with pytest.raises(AuditCanonicalizationError):
        canonicalize_metadata({"request_id": object()})
    with pytest.raises(AuditCanonicalizationError):
        canonicalize_datetime(datetime(2026, 7, 24, 14, 30, 0))  # noqa: DTZ001

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.audit_event import ALLOWED_METADATA_KEYS, AuditEvent
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _event(**overrides: object) -> AuditEvent:
    defaults = {
        "id": AuditEventId(value=uuid4()),
        "actor_user_id": UserId(value=uuid4()),
        "authorization_organization_id": OrganizationId(value=uuid4()),
        "target_organization_id": None,
        "action": AuditAction.USER_CREATE,
        "resource_type": AuditResourceType.USER,
        "resource_id": uuid4(),
        "outcome": AuditOutcome.SUCCESS,
        "failure_code": None,
        "metadata": {"changed_fields": ["display_name"]},
        "occurred_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)


def test_audit_event_is_immutable() -> None:
    event = _event()

    with pytest.raises(Exception):
        event.action = AuditAction.USER_UPDATE  # type: ignore[misc]


def test_audit_event_rejects_unknown_metadata_keys() -> None:
    with pytest.raises(ValueError, match="Unsupported audit metadata keys"):
        _event(metadata={"password": "secret"})


def test_audit_event_accepts_allowlisted_metadata_keys() -> None:
    event = _event(
        metadata={
            "changed_fields": ["name"],
            "previous_role": "member",
            "new_role": "admin",
            "previous_status": "ACTIVE",
            "new_status": "DEACTIVATED",
            "expiration_refreshed": True,
            "membership_id": str(uuid4()),
        }
    )

    assert set(event.metadata) <= ALLOWED_METADATA_KEYS


def test_audit_event_supports_optional_actor_and_organization_fields() -> None:
    event = _event(
        actor_user_id=None,
        authorization_organization_id=None,
        resource_id=None,
    )

    assert event.actor_user_id is None
    assert event.authorization_organization_id is None
    assert event.resource_id is None


def test_audit_event_normalizes_failure_code() -> None:
    event = _event(outcome=AuditOutcome.FAILURE, failure_code="  Duplicate_User_Email  ")

    assert event.failure_code == "duplicate_user_email"


def test_audit_action_values_are_stable() -> None:
    assert AuditAction.USER_CREATE.value == "user.create"
    assert AuditAction.INVITATION_ACCEPT.value == "invitation.accept"


def test_audit_resource_types_are_stable() -> None:
    assert AuditResourceType.USER.value == "USER"
    assert AuditResourceType.INVITATION.value == "INVITATION"


def test_audit_outcomes_are_success_and_failure_only() -> None:
    assert {member.value for member in AuditOutcome} == {"SUCCESS", "FAILURE"}

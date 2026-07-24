from __future__ import annotations

import dataclasses

import pytest

from backend.core.domain.security_events import (
    SECURITY_EVENT_REGISTRY,
    SecurityEventCategory,
    SecurityEventDescriptor,
    SecurityEventProducerOwner,
    SecurityEventSignificance,
    SecurityEventSubjectDomain,
    is_preferred_event_type_identifier,
    security_event_descriptor_for,
    security_event_types,
    validate_event_type_identifier_for_registration,
    validate_security_event_registry,
)
from backend.core.domain.security_events.families.administrative import (
    ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS,
)
from backend.core.domain.security_events.families.authorization import (
    AUTHORIZATION_SECURITY_EVENT_DESCRIPTORS,
)
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def test_registry_contains_every_published_audit_action() -> None:
    published_actions = {action.value for action in AuditAction}
    registered_types = security_event_types()

    assert registered_types == published_actions


def test_registry_has_seventeen_published_descriptors() -> None:
    assert len(SECURITY_EVENT_REGISTRY) == 17
    assert len(ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS) == 16
    assert len(AUTHORIZATION_SECURITY_EVENT_DESCRIPTORS) == 1


def test_descriptor_immutability() -> None:
    descriptor = security_event_descriptor_for("user.create")
    assert descriptor is not None

    with pytest.raises(dataclasses.FrozenInstanceError):
        descriptor.event_type = "user.updated"  # type: ignore[misc]


def test_event_type_uniqueness_validation_rejects_duplicates() -> None:
    original = security_event_descriptor_for("user.create")
    assert original is not None
    duplicate = SecurityEventDescriptor(
        event_type=original.event_type,
        category=original.category,
        subject_domain=original.subject_domain,
        producer_owner=original.producer_owner,
        allowed_outcomes=original.allowed_outcomes,
        legacy_identifier=original.legacy_identifier,
    )

    with pytest.raises(ValueError, match="Duplicate security event type"):
        validate_security_event_registry(frozenset({original, duplicate}))


def test_authorization_permission_denied_descriptor() -> None:
    descriptor = security_event_descriptor_for("authorization.permission_denied")
    assert descriptor is not None
    assert descriptor.category is SecurityEventCategory.AUTHORIZATION
    assert descriptor.subject_domain is SecurityEventSubjectDomain.SECURITY_SYSTEM
    assert descriptor.producer_owner is SecurityEventProducerOwner.AUTHORIZATION
    assert descriptor.allowed_outcomes == frozenset({AuditOutcome.FAILURE})
    assert descriptor.default_security_significance is SecurityEventSignificance.MEDIUM
    assert descriptor.legacy_identifier is True


def test_administrative_descriptors_share_producer_and_outcomes() -> None:
    for descriptor in ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS:
        assert descriptor.category is SecurityEventCategory.ADMINISTRATIVE
        assert descriptor.producer_owner is SecurityEventProducerOwner.ADMINISTRATIVE_AUDIT
        assert descriptor.allowed_outcomes == frozenset(
            {AuditOutcome.SUCCESS, AuditOutcome.FAILURE}
        )
        assert descriptor.legacy_identifier is True


def test_preferred_naming_convention_examples() -> None:
    assert is_preferred_event_type_identifier("authentication.credential.rejected") is True
    assert is_preferred_event_type_identifier("administrative.invitation.revoked") is True
    assert is_preferred_event_type_identifier("user.create") is False
    assert is_preferred_event_type_identifier("authorization.permission_denied") is False


def test_new_non_compliant_identifier_requires_legacy_flag() -> None:
    with pytest.raises(ValueError, match="preferred"):
        validate_event_type_identifier_for_registration(
            "user.create",
            legacy_identifier=False,
        )

    validate_event_type_identifier_for_registration(
        "user.create",
        legacy_identifier=True,
    )


def test_new_compliant_identifier_does_not_require_legacy_flag() -> None:
    validate_event_type_identifier_for_registration(
        "authentication.session.created",
        legacy_identifier=False,
    )


def test_registry_validation_rejects_empty_outcomes() -> None:
    invalid = SecurityEventDescriptor(
        event_type="authentication.session.created",
        category=SecurityEventCategory.AUTHENTICATION,
        subject_domain=SecurityEventSubjectDomain.SESSION,
        producer_owner=SecurityEventProducerOwner.AUTHENTICATION,
        allowed_outcomes=frozenset(),
    )

    with pytest.raises(ValueError, match="at least one outcome"):
        validate_security_event_registry(frozenset({invalid}))

from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.naming import validate_event_type_identifier_for_registration
from backend.core.domain.security_events.producer_owners import SecurityEventProducerOwner
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.security_events.subject_domains import SecurityEventSubjectDomain
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def validate_security_event_registry(
    registry: frozenset[SecurityEventDescriptor],
) -> None:
    if not registry:
        raise ValueError("Security event registry must not be empty.")

    seen_event_types: set[str] = set()
    for descriptor in registry:
        _validate_descriptor(descriptor)
        if descriptor.event_type in seen_event_types:
            raise ValueError(
                f"Duplicate security event type registration: {descriptor.event_type!r}."
            )
        seen_event_types.add(descriptor.event_type)


def _validate_descriptor(descriptor: SecurityEventDescriptor) -> None:
    validate_event_type_identifier_for_registration(
        descriptor.event_type,
        legacy_identifier=descriptor.legacy_identifier,
    )
    _validate_enum_value(descriptor.category, SecurityEventCategory, "category")
    _validate_enum_value(descriptor.subject_domain, SecurityEventSubjectDomain, "subject domain")
    _validate_enum_value(descriptor.producer_owner, SecurityEventProducerOwner, "producer owner")
    if not descriptor.allowed_outcomes:
        raise ValueError(
            f"Security event descriptor {descriptor.event_type!r} must allow at least one outcome."
        )
    for outcome in descriptor.allowed_outcomes:
        _validate_enum_value(outcome, AuditOutcome, "outcome")
    if descriptor.default_security_significance is not None:
        _validate_enum_value(
            descriptor.default_security_significance,
            SecurityEventSignificance,
            "default security significance",
        )


def _validate_enum_value(value: object, enum_type: type, label: str) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"Invalid {label} value: {value!r}.")

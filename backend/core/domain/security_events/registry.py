from __future__ import annotations

from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.families.administrative import (
    ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS,
)
from backend.core.domain.security_events.families.authorization import (
    AUTHORIZATION_SECURITY_EVENT_DESCRIPTORS,
)
from backend.core.domain.security_events.validation import validate_security_event_registry

_ALL_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    *ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS,
    *AUTHORIZATION_SECURITY_EVENT_DESCRIPTORS,
)

SECURITY_EVENT_REGISTRY: frozenset[SecurityEventDescriptor] = frozenset(_ALL_DESCRIPTORS)

_EVENT_TYPE_INDEX: dict[str, SecurityEventDescriptor] = {
    descriptor.event_type: descriptor for descriptor in _ALL_DESCRIPTORS
}


def security_event_types() -> frozenset[str]:
    return frozenset(_EVENT_TYPE_INDEX)


def security_event_descriptor_for(event_type: str) -> SecurityEventDescriptor | None:
    return _EVENT_TYPE_INDEX.get(event_type)


def published_security_event_registry() -> frozenset[SecurityEventDescriptor]:
    """Return the immutable registry of currently published security event types."""
    return SECURITY_EVENT_REGISTRY


validate_security_event_registry(SECURITY_EVENT_REGISTRY)

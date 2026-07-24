from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.registry import (
    SECURITY_EVENT_REGISTRY,
    security_event_descriptor_for,
)
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.value_objects.audit_action import AuditAction


class UnknownSecurityEventNameError(ValueError):
    """Raised when a claimed taxonomy event name is not registered."""


def resolve_security_event_name(event_name: str) -> AuditAction:
    """Resolve a canonical taxonomy event name to ``AuditAction``.

    Rejects unknown names rather than treating them as empty result filters.
    """

    normalized = event_name.strip()
    if not normalized:
        raise UnknownSecurityEventNameError("Security event name must not be empty.")
    descriptor = security_event_descriptor_for(normalized)
    if descriptor is None:
        raise UnknownSecurityEventNameError(
            f"Unknown security event name: {normalized!r}."
        )
    try:
        return AuditAction(normalized)
    except ValueError as exc:
        raise UnknownSecurityEventNameError(
            f"Unknown security event name: {normalized!r}."
        ) from exc


def audit_actions_for_category(
    category: SecurityEventCategory,
) -> frozenset[AuditAction]:
    return frozenset(
        AuditAction(descriptor.event_type)
        for descriptor in SECURITY_EVENT_REGISTRY
        if descriptor.category is category
    )


def audit_actions_for_significance(
    significance: SecurityEventSignificance,
) -> frozenset[AuditAction]:
    return frozenset(
        AuditAction(descriptor.event_type)
        for descriptor in SECURITY_EVENT_REGISTRY
        if descriptor.default_security_significance is significance
    )


def intersect_action_filters(
    *candidates: frozenset[AuditAction] | None,
) -> frozenset[AuditAction] | None:
    """AND-combine optional action sets.

    ``None`` means "no constraint". An empty frozenset means "match nothing".
    """

    combined: frozenset[AuditAction] | None = None
    for candidate in candidates:
        if candidate is None:
            continue
        combined = candidate if combined is None else combined & candidate
    return combined

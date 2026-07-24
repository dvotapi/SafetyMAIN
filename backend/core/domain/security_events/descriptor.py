from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.producer_owners import SecurityEventProducerOwner
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.security_events.subject_domains import SecurityEventSubjectDomain
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


@dataclass(frozen=True, slots=True)
class SecurityEventDescriptor:
    """Immutable taxonomy metadata for one published persisted security event type."""

    event_type: str
    category: SecurityEventCategory
    subject_domain: SecurityEventSubjectDomain
    producer_owner: SecurityEventProducerOwner
    allowed_outcomes: frozenset[AuditOutcome]
    legacy_identifier: bool = False
    default_security_significance: SecurityEventSignificance | None = None
    description: str | None = None

from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.producer_owners import SecurityEventProducerOwner
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.security_events.subject_domains import SecurityEventSubjectDomain
from backend.core.domain.value_objects.audit_outcome import AuditOutcome

AUTHORIZATION_SECURITY_EVENT_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    SecurityEventDescriptor(
        event_type="authorization.permission_denied",
        category=SecurityEventCategory.AUTHORIZATION,
        subject_domain=SecurityEventSubjectDomain.SECURITY_SYSTEM,
        producer_owner=SecurityEventProducerOwner.AUTHORIZATION,
        allowed_outcomes=frozenset({AuditOutcome.FAILURE}),
        legacy_identifier=True,
        default_security_significance=SecurityEventSignificance.MEDIUM,
        description=(
            "Centralized authorization boundary denied a required permission "
            "for an authenticated actor with trusted tenant context."
        ),
    ),
)

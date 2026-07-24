from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.producer_owners import (
    SecurityEventProducerOwner,
)
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.security_events.subject_domains import (
    SecurityEventSubjectDomain,
)
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def _authentication_descriptor(
    *,
    event_type: str,
    allowed_outcome: AuditOutcome,
    significance: SecurityEventSignificance,
    description: str,
) -> SecurityEventDescriptor:
    return SecurityEventDescriptor(
        event_type=event_type,
        category=SecurityEventCategory.AUTHENTICATION,
        subject_domain=SecurityEventSubjectDomain.SESSION,
        producer_owner=SecurityEventProducerOwner.AUTHENTICATION,
        allowed_outcomes=frozenset({allowed_outcome}),
        legacy_identifier=False,
        default_security_significance=significance,
        description=description,
    )


AUTHENTICATION_SECURITY_EVENT_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    _authentication_descriptor(
        event_type="authentication.login.succeeded",
        allowed_outcome=AuditOutcome.SUCCESS,
        significance=SecurityEventSignificance.INFORMATIONAL,
        description=(
            "Password authentication succeeded and access/refresh tokens were issued."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.login.failed",
        allowed_outcome=AuditOutcome.FAILURE,
        significance=SecurityEventSignificance.MEDIUM,
        description=(
            "Password authentication was denied for normalized credential or eligibility "
            "failure reasons."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.refresh.succeeded",
        allowed_outcome=AuditOutcome.SUCCESS,
        significance=SecurityEventSignificance.INFORMATIONAL,
        description=(
            "Refresh token validation succeeded and a new authentication token pair "
            "was issued."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.refresh.failed",
        allowed_outcome=AuditOutcome.FAILURE,
        significance=SecurityEventSignificance.MEDIUM,
        description=(
            "Refresh token validation or rotation was denied for a normalized token "
            "failure reason."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.logout.succeeded",
        allowed_outcome=AuditOutcome.SUCCESS,
        significance=SecurityEventSignificance.INFORMATIONAL,
        description=(
            "A refresh session was revoked through logout, or logout completed "
            "idempotently for an unusable refresh token."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.refresh.reused",
        allowed_outcome=AuditOutcome.FAILURE,
        significance=SecurityEventSignificance.HIGH,
        description=(
            "A previously rotated refresh token was presented; the refresh-token "
            "family was revoked as a compromise response."
        ),
    ),
    _authentication_descriptor(
        event_type="authentication.session.revoked",
        allowed_outcome=AuditOutcome.SUCCESS,
        significance=SecurityEventSignificance.MEDIUM,
        description=(
            "One or more refresh sessions were revoked for an administrative or "
            "security reason such as user deactivation."
        ),
    ),
)

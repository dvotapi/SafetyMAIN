from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.producer_owners import SecurityEventProducerOwner
from backend.core.domain.security_events.subject_domains import SecurityEventSubjectDomain
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def _administrative_descriptor(
    *,
    event_type: str,
    subject_domain: SecurityEventSubjectDomain,
    description: str,
) -> SecurityEventDescriptor:
    return SecurityEventDescriptor(
        event_type=event_type,
        category=SecurityEventCategory.ADMINISTRATIVE,
        subject_domain=subject_domain,
        producer_owner=SecurityEventProducerOwner.ADMINISTRATIVE_AUDIT,
        allowed_outcomes=frozenset({AuditOutcome.SUCCESS, AuditOutcome.FAILURE}),
        legacy_identifier=True,
        description=description,
    )


ADMINISTRATIVE_SECURITY_EVENT_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    _administrative_descriptor(
        event_type="user.create",
        subject_domain=SecurityEventSubjectDomain.USER,
        description="Administrative user creation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="user.update",
        subject_domain=SecurityEventSubjectDomain.USER,
        description="Administrative user update completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="user.activate",
        subject_domain=SecurityEventSubjectDomain.USER,
        description="Administrative user activation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="user.deactivate",
        subject_domain=SecurityEventSubjectDomain.USER,
        description="Administrative user deactivation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="organization.create",
        subject_domain=SecurityEventSubjectDomain.ORGANIZATION,
        description="Administrative organization creation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="organization.update",
        subject_domain=SecurityEventSubjectDomain.ORGANIZATION,
        description="Administrative organization update completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="organization.activate",
        subject_domain=SecurityEventSubjectDomain.ORGANIZATION,
        description="Administrative organization activation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="organization.deactivate",
        subject_domain=SecurityEventSubjectDomain.ORGANIZATION,
        description="Administrative organization deactivation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="membership.create",
        subject_domain=SecurityEventSubjectDomain.MEMBERSHIP,
        description="Administrative membership creation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="membership.role_change",
        subject_domain=SecurityEventSubjectDomain.MEMBERSHIP,
        description="Administrative membership role change completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="membership.activate",
        subject_domain=SecurityEventSubjectDomain.MEMBERSHIP,
        description="Administrative membership activation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="membership.deactivate",
        subject_domain=SecurityEventSubjectDomain.MEMBERSHIP,
        description="Administrative membership deactivation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="invitation.create",
        subject_domain=SecurityEventSubjectDomain.INVITATION,
        description="Administrative invitation creation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="invitation.revoke",
        subject_domain=SecurityEventSubjectDomain.INVITATION,
        description="Administrative invitation revocation completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="invitation.reissue",
        subject_domain=SecurityEventSubjectDomain.INVITATION,
        description="Administrative invitation reissue completed or rejected.",
    ),
    _administrative_descriptor(
        event_type="invitation.accept",
        subject_domain=SecurityEventSubjectDomain.INVITATION,
        description="Invitation acceptance completed or rejected.",
    ),
)

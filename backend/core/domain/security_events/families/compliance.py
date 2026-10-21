from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.producer_owners import (
    SecurityEventProducerOwner,
)
from backend.core.domain.security_events.subject_domains import (
    SecurityEventSubjectDomain,
)
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def _compliance_descriptor(
    *,
    event_type: str,
    description: str,
    legacy_identifier: bool = False,
) -> SecurityEventDescriptor:
    return SecurityEventDescriptor(
        event_type=event_type,
        category=SecurityEventCategory.ADMINISTRATIVE,
        subject_domain=SecurityEventSubjectDomain.COMPLIANCE_DOCUMENT,
        producer_owner=SecurityEventProducerOwner.ADMINISTRATIVE_AUDIT,
        allowed_outcomes=frozenset({AuditOutcome.SUCCESS, AuditOutcome.FAILURE}),
        legacy_identifier=legacy_identifier,
        description=description,
    )


# Phase 4 writes only ``created`` and ``updated``; the other identifiers are
# reserved so Phase 5 can wire lifecycle and file actions without changing the
# registry. ``review_started``, ``review_completed`` and ``file_attached`` do
# not match ``<category>.<subject>.<action>`` and are marked legacy identifiers
# (D5), like the Risk Control precedents.
COMPLIANCE_SECURITY_EVENT_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    _compliance_descriptor(
        event_type="compliance.document.created",
        description="Compliance document creation completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.updated",
        description="Compliance document update completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.approved",
        description="Compliance document approval completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.activated",
        description="Compliance document activation completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.review_started",
        description="Compliance document review start completed or rejected.",
        legacy_identifier=True,
    ),
    _compliance_descriptor(
        event_type="compliance.document.review_completed",
        description="Compliance document review completion completed or rejected.",
        legacy_identifier=True,
    ),
    _compliance_descriptor(
        event_type="compliance.document.superseded",
        description="Compliance document supersession completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.archived",
        description="Compliance document archival completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.restored",
        description="Compliance document restoration completed or rejected.",
    ),
    _compliance_descriptor(
        event_type="compliance.document.file_attached",
        description="Compliance document file attachment completed or rejected.",
        legacy_identifier=True,
    ),
)

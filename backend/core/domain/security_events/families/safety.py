from __future__ import annotations

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.descriptor import SecurityEventDescriptor
from backend.core.domain.security_events.producer_owners import SecurityEventProducerOwner
from backend.core.domain.security_events.subject_domains import SecurityEventSubjectDomain
from backend.core.domain.value_objects.audit_outcome import AuditOutcome


def _safety_descriptor(
    *,
    event_type: str,
    description: str,
    subject_domain: SecurityEventSubjectDomain = SecurityEventSubjectDomain.HAZARD,
    legacy_identifier: bool = False,
) -> SecurityEventDescriptor:
    return SecurityEventDescriptor(
        event_type=event_type,
        category=SecurityEventCategory.ADMINISTRATIVE,
        subject_domain=subject_domain,
        producer_owner=SecurityEventProducerOwner.ADMINISTRATIVE_AUDIT,
        allowed_outcomes=frozenset({AuditOutcome.SUCCESS, AuditOutcome.FAILURE}),
        legacy_identifier=legacy_identifier,
        description=description,
    )


SAFETY_SECURITY_EVENT_DESCRIPTORS: tuple[SecurityEventDescriptor, ...] = (
    _safety_descriptor(
        event_type="safety.hazard.created",
        description="Hazard record creation completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.hazard.updated",
        description="Hazard descriptive update completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.hazard.activated",
        description="Hazard activation completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.hazard.archived",
        description="Hazard archival completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.hazard.restored",
        description="Hazard restoration from archive completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk.created",
        subject_domain=SecurityEventSubjectDomain.RISK,
        description="Risk assessment creation completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk.updated",
        subject_domain=SecurityEventSubjectDomain.RISK,
        description="Risk assessment update completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk.approved",
        subject_domain=SecurityEventSubjectDomain.RISK,
        description="Risk assessment approval completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk.superseded",
        subject_domain=SecurityEventSubjectDomain.RISK,
        description="Risk assessment supersession completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk.archived",
        subject_domain=SecurityEventSubjectDomain.RISK,
        description="Risk assessment archival completed or rejected.",
    ),
    _safety_descriptor(
        event_type="safety.risk_control.created",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control creation completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.updated",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control update completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.owner_assigned",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control owner assignment completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.owner_changed",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control owner change completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.planned",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control planning completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.implementation_started",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control implementation start completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.progress_updated",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control progress update completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.evidence_added",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control evidence addition completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.implemented",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control implementation completion completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.verification_recorded",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control verification recording completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.verified_effective",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control verified effective completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.verified_partially_effective",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control partially effective verification completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.verified_ineffective",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control ineffective verification completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.review_scheduled",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control review scheduling completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.review_completed",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control review completion completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.suspended",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control suspension completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.resumed",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control resume completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.superseded",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control supersession completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.archived",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control archival completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.cancelled",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control cancellation completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.materialized",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control materialization from assessment completed or rejected.",
        legacy_identifier=True,
    ),
    _safety_descriptor(
        event_type="safety.risk_control.correction_recorded",
        subject_domain=SecurityEventSubjectDomain.RISK_CONTROL,
        description="Risk control correction recording completed or rejected.",
        legacy_identifier=True,
    ),
)

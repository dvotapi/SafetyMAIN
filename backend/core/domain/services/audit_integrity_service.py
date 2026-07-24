from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_event_canonicalizer import (
    canonical_audit_event_bytes,
    resolve_audit_chain_organization_id,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_chain_head import AuditChainHead
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_integrity import (
    CURRENT_AUDIT_INTEGRITY_VERSION,
    AuditIntegrityHash,
    AuditIntegrityVersion,
)


class AuditIntegrityFailureReason(str, Enum):
    MISSING_INTEGRITY_HASH = "missing_integrity_hash"
    INVALID_INTEGRITY_HASH_FORMAT = "invalid_integrity_hash_format"
    PREVIOUS_HASH_MISMATCH = "previous_hash_mismatch"
    EVENT_HASH_MISMATCH = "event_hash_mismatch"
    UNSUPPORTED_INTEGRITY_VERSION = "unsupported_integrity_version"
    UNEXPECTED_GENESIS = "unexpected_genesis"
    CHAIN_HEAD_MISMATCH = "chain_head_mismatch"
    CHAIN_FORK = "chain_fork"


@dataclass(frozen=True, slots=True)
class AuditChainVerificationResult:
    organization_id: OrganizationId
    valid: bool
    checked_event_count: int
    first_invalid_event_id: AuditEventId | None
    reason: AuditIntegrityFailureReason | None


def order_events_by_integrity_links(
    events: Sequence[AuditEvent],
) -> tuple[tuple[AuditEvent, ...] | None, AuditEventId | None]:
    """Order events by previous→next integrity links.

    Returns ``(ordered_events, None)`` on success, or ``(None, first_invalid_id)``
    when the graph is not a single chain (fork, cycle, or disconnected nodes).
    Concurrent writers may produce timestamps that do not match append order; hash
    links are the authoritative chain order.
    """

    if not events:
        return (), None

    for event in events:
        if event.integrity_hash is None:
            return None, event.id

    by_previous: dict[str | None, list[AuditEvent]] = {}
    for event in events:
        key = (
            event.previous_integrity_hash.value
            if event.previous_integrity_hash is not None
            else None
        )
        by_previous.setdefault(key, []).append(event)

    genesis_candidates = by_previous.get(None, [])
    if len(genesis_candidates) != 1:
        invalid = genesis_candidates[0].id if genesis_candidates else events[0].id
        return None, invalid

    ordered: list[AuditEvent] = []
    current: AuditEvent | None = genesis_candidates[0]
    seen: set[AuditEventId] = set()
    while current is not None:
        if current.id in seen:
            return None, current.id
        seen.add(current.id)
        ordered.append(current)
        if current.integrity_hash is None:
            return None, current.id
        successors = by_previous.get(current.integrity_hash.value, [])
        if len(successors) > 1:
            return None, successors[0].id
        current = successors[0] if successors else None

    if len(ordered) != len(events):
        missing = next(event for event in events if event.id not in seen)
        return None, missing.id
    return tuple(ordered), None


class AuditIntegrityService:
    """Deterministic SHA-256 integrity finalization and chain verification."""

    def finalize_event(
        self,
        event: AuditEvent,
        previous_hash: AuditIntegrityHash | None,
        *,
        integrity_version: AuditIntegrityVersion = CURRENT_AUDIT_INTEGRITY_VERSION,
    ) -> AuditEvent:
        digest = self.compute_integrity_hash(
            event,
            previous_hash=previous_hash,
            integrity_version=integrity_version,
        )
        return event.model_copy(
            update={
                "previous_integrity_hash": previous_hash,
                "integrity_hash": digest,
                "integrity_version": integrity_version,
            }
        )

    def compute_integrity_hash(
        self,
        event: AuditEvent,
        *,
        previous_hash: AuditIntegrityHash | None,
        integrity_version: AuditIntegrityVersion = CURRENT_AUDIT_INTEGRITY_VERSION,
    ) -> AuditIntegrityHash:
        if integrity_version.value != CURRENT_AUDIT_INTEGRITY_VERSION.value:
            raise ValueError(
                f"Unsupported audit integrity version for hashing: {integrity_version.value}."
            )
        previous_value = previous_hash.value if previous_hash is not None else None
        payload = canonical_audit_event_bytes(
            event,
            previous_integrity_hash=previous_value,
            integrity_version=integrity_version,
        )
        return AuditIntegrityHash(value=hashlib.sha256(payload).hexdigest())

    def verify_chain(
        self,
        organization_id: OrganizationId,
        events: Sequence[AuditEvent],
        *,
        chain_head: AuditChainHead | None = None,
    ) -> AuditChainVerificationResult:
        if not events and chain_head is not None:
            return AuditChainVerificationResult(
                organization_id=organization_id,
                valid=False,
                checked_event_count=0,
                first_invalid_event_id=chain_head.latest_audit_event_id,
                reason=AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH,
            )

        ordered, fork_event_id = order_events_by_integrity_links(events)
        if ordered is None:
            return AuditChainVerificationResult(
                organization_id=organization_id,
                valid=False,
                checked_event_count=0,
                first_invalid_event_id=fork_event_id,
                reason=AuditIntegrityFailureReason.CHAIN_FORK,
            )

        expected_previous: AuditIntegrityHash | None = None
        for index, event in enumerate(ordered):
            if event.integrity_hash is None or event.integrity_version is None:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.MISSING_INTEGRITY_HASH,
                )

            if event.integrity_version.value != CURRENT_AUDIT_INTEGRITY_VERSION.value:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.UNSUPPORTED_INTEGRITY_VERSION,
                )

            try:
                AuditIntegrityHash(value=event.integrity_hash.value)
            except ValueError:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.INVALID_INTEGRITY_HASH_FORMAT,
                )

            if index == 0:
                if event.previous_integrity_hash is not None:
                    return AuditChainVerificationResult(
                        organization_id=organization_id,
                        valid=False,
                        checked_event_count=index,
                        first_invalid_event_id=event.id,
                        reason=AuditIntegrityFailureReason.PREVIOUS_HASH_MISMATCH,
                    )
            elif event.previous_integrity_hash is None:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.UNEXPECTED_GENESIS,
                )
            elif event.previous_integrity_hash != expected_previous:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.PREVIOUS_HASH_MISMATCH,
                )

            chain_org = resolve_audit_chain_organization_id(event)
            if chain_org != organization_id:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.PREVIOUS_HASH_MISMATCH,
                )

            expected_hash = self.compute_integrity_hash(
                event,
                previous_hash=event.previous_integrity_hash,
                integrity_version=event.integrity_version,
            )
            if event.integrity_hash != expected_hash:
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=index,
                    first_invalid_event_id=event.id,
                    reason=AuditIntegrityFailureReason.EVENT_HASH_MISMATCH,
                )

            expected_previous = event.integrity_hash

        if ordered and chain_head is None:
            return AuditChainVerificationResult(
                organization_id=organization_id,
                valid=False,
                checked_event_count=len(ordered),
                first_invalid_event_id=ordered[-1].id,
                reason=AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH,
            )

        if ordered and chain_head is not None:
            last = ordered[-1]
            assert last.integrity_hash is not None
            assert last.integrity_version is not None
            if (
                chain_head.organization_id != organization_id
                or chain_head.latest_audit_event_id != last.id
                or chain_head.latest_integrity_hash != last.integrity_hash
                or chain_head.integrity_version != last.integrity_version
            ):
                return AuditChainVerificationResult(
                    organization_id=organization_id,
                    valid=False,
                    checked_event_count=len(ordered),
                    first_invalid_event_id=last.id,
                    reason=AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH,
                )

        return AuditChainVerificationResult(
            organization_id=organization_id,
            valid=True,
            checked_event_count=len(ordered),
            first_invalid_event_id=None,
            reason=None,
        )

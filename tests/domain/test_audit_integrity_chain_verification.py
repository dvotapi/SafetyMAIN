from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.services.audit_integrity_service import (
    AuditIntegrityFailureReason,
    AuditIntegrityService,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_chain_head import AuditChainHead
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_integrity import (
    CURRENT_AUDIT_INTEGRITY_VERSION,
    AuditIntegrityHash,
    AuditIntegrityVersion,
)
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

ORG = OrganizationId(value=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"))


def _draft(*, event_id: UUID | None = None, occurred_at: datetime | None = None) -> AuditEvent:
    return AuditEvent(
        id=AuditEventId(value=event_id or uuid4()),
        actor_user_id=UserId(value=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")),
        authorization_organization_id=ORG,
        target_organization_id=None,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=uuid4(),
        outcome=AuditOutcome.SUCCESS,
        failure_code=None,
        metadata={"request_id": "req"},
        occurred_at=occurred_at or datetime.now(UTC),
    )


def _chain(count: int) -> tuple[AuditEvent, ...]:
    service = AuditIntegrityService()
    events: list[AuditEvent] = []
    previous = None
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for index in range(count):
        draft = _draft(occurred_at=base + timedelta(seconds=index))
        finalized = service.finalize_event(draft, previous)
        events.append(finalized)
        previous = finalized.integrity_hash
    return tuple(events)


def _head(events: tuple[AuditEvent, ...] | list[AuditEvent]) -> AuditChainHead:
    last = events[-1]
    assert last.integrity_hash is not None
    assert last.integrity_version is not None
    return AuditChainHead(
        organization_id=ORG,
        latest_audit_event_id=last.id,
        latest_integrity_hash=last.integrity_hash,
        integrity_version=last.integrity_version,
    )


def test_empty_chain_is_valid() -> None:
    result = AuditIntegrityService().verify_chain(ORG, (), chain_head=None)
    assert result.valid is True
    assert result.checked_event_count == 0


def test_empty_events_with_chain_head_is_invalid() -> None:
    phantom = AuditChainHead(
        organization_id=ORG,
        latest_audit_event_id=AuditEventId(value=uuid4()),
        latest_integrity_hash=AuditIntegrityHash(value="a" * 64),
        integrity_version=CURRENT_AUDIT_INTEGRITY_VERSION,
    )
    result = AuditIntegrityService().verify_chain(ORG, (), chain_head=phantom)
    assert result.valid is False
    assert result.reason is AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH


def test_single_and_multiple_valid_events() -> None:
    service = AuditIntegrityService()
    single = _chain(1)
    assert service.verify_chain(ORG, single, chain_head=_head(single)).valid is True
    multi = _chain(3)
    assert service.verify_chain(ORG, multi, chain_head=_head(multi)).valid is True
    assert multi[0].previous_integrity_hash is None
    assert multi[1].previous_integrity_hash == multi[0].integrity_hash


def test_events_without_chain_head_are_invalid() -> None:
    events = _chain(1)
    result = AuditIntegrityService().verify_chain(ORG, events, chain_head=None)
    assert result.valid is False
    assert result.reason is AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH


def test_final_event_deletion_detected_via_chain_head() -> None:
    events = _chain(3)
    remaining = events[:-1]
    result = AuditIntegrityService().verify_chain(
        ORG,
        remaining,
        chain_head=_head(events),
    )
    assert result.valid is False
    assert result.reason is AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH
    assert result.first_invalid_event_id == remaining[-1].id


def test_detects_modified_fields_and_previous_hash() -> None:
    service = AuditIntegrityService()
    events = list(_chain(3))
    head = _head(events)

    tampered_metadata = events[1].model_copy(
        update={"metadata": {"request_id": "tampered"}}
    )
    result = service.verify_chain(
        ORG,
        (events[0], tampered_metadata, events[2]),
        chain_head=head,
    )
    assert result.valid is False
    assert result.first_invalid_event_id == events[1].id
    assert result.reason is AuditIntegrityFailureReason.EVENT_HASH_MISMATCH

    tampered_time = events[1].model_copy(
        update={"occurred_at": events[1].occurred_at + timedelta(seconds=1)}
    )
    assert (
        service.verify_chain(
            ORG, (events[0], tampered_time, events[2]), chain_head=head
        ).reason
        is AuditIntegrityFailureReason.EVENT_HASH_MISMATCH
    )

    tampered_actor = events[1].model_copy(
        update={"actor_user_id": UserId(value=uuid4())}
    )
    assert (
        service.verify_chain(
            ORG, (events[0], tampered_actor, events[2]), chain_head=head
        ).reason
        is AuditIntegrityFailureReason.EVENT_HASH_MISMATCH
    )

    tampered_action = events[1].model_copy(update={"action": AuditAction.USER_UPDATE})
    assert (
        service.verify_chain(
            ORG, (events[0], tampered_action, events[2]), chain_head=head
        ).reason
        is AuditIntegrityFailureReason.EVENT_HASH_MISMATCH
    )

    broken_link = events[1].model_copy(
        update={"previous_integrity_hash": AuditIntegrityHash(value="0" * 64)}
    )
    assert (
        service.verify_chain(
            ORG, (events[0], broken_link, events[2]), chain_head=head
        ).reason
        is AuditIntegrityFailureReason.CHAIN_FORK
    )


def test_detects_deletion_reordering_insertion_and_second_genesis() -> None:
    service = AuditIntegrityService()
    events = list(_chain(3))
    head = _head(events)

    deleted_middle = (events[0], events[2])
    assert (
        service.verify_chain(ORG, deleted_middle, chain_head=head).reason
        is AuditIntegrityFailureReason.CHAIN_FORK
    )

    reordered = (events[0], events[2], events[1])
    # Presentation order is not authoritative; hash-link order remains valid.
    assert service.verify_chain(ORG, reordered, chain_head=head).valid is True

    inserted = service.finalize_event(_draft(), events[0].integrity_hash)
    with_insert = (events[0], inserted, events[1], events[2])
    assert service.verify_chain(ORG, with_insert, chain_head=head).valid is False

    second_genesis = events[1].model_copy(update={"previous_integrity_hash": None})
    assert (
        service.verify_chain(
            ORG, (events[0], second_genesis, events[2]), chain_head=head
        ).reason
        is AuditIntegrityFailureReason.CHAIN_FORK
    )


def test_detects_missing_invalid_and_unsupported_integrity() -> None:
    service = AuditIntegrityService()
    events = list(_chain(1))
    head = _head(events)
    missing = events[0].model_copy(
        update={"integrity_hash": None, "integrity_version": None}
    )
    assert (
        service.verify_chain(ORG, (missing,), chain_head=head).reason
        is AuditIntegrityFailureReason.CHAIN_FORK
    )

    unsupported = events[0].model_copy(
        update={"integrity_version": AuditIntegrityVersion(value=99)}
    )
    assert (
        service.verify_chain(ORG, (unsupported,), chain_head=head).reason
        is AuditIntegrityFailureReason.UNSUPPORTED_INTEGRITY_VERSION
    )
    assert CURRENT_AUDIT_INTEGRITY_VERSION.value == 1


def test_detects_chain_head_pointer_tampering() -> None:
    events = _chain(2)
    head = _head(events)
    tampered = AuditChainHead(
        organization_id=ORG,
        latest_audit_event_id=events[0].id,
        latest_integrity_hash=events[0].integrity_hash,  # type: ignore[arg-type]
        integrity_version=events[0].integrity_version,  # type: ignore[arg-type]
    )
    result = AuditIntegrityService().verify_chain(ORG, events, chain_head=tampered)
    assert result.valid is False
    assert result.reason is AuditIntegrityFailureReason.CHAIN_HEAD_MISMATCH
    assert head.latest_audit_event_id == events[1].id

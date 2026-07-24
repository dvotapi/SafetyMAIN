from __future__ import annotations

import threading

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound
from backend.core.domain.repositories.audit_event_repository import (
    AuditEventRepositoryContract,
)
from backend.core.domain.services.audit_event_canonicalizer import (
    resolve_audit_chain_organization_id,
)
from backend.core.domain.services.audit_integrity_service import AuditIntegrityService
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_chain_head import AuditChainHead
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
    effective_actions,
)
from backend.core.domain.value_objects.audit_integrity import (
    CURRENT_AUDIT_INTEGRITY_VERSION,
    AuditIntegrityHash,
)


def _is_in_scope(event: AuditEvent, criteria: AuditEventListCriteria) -> bool:
    scope_id = criteria.scope_organization_id
    return (
        event.authorization_organization_id == scope_id
        or event.target_organization_id == scope_id
    )


def _belongs_to_chain(event: AuditEvent, organization_id: OrganizationId) -> bool:
    return resolve_audit_chain_organization_id(event) == organization_id


class InMemoryAuditEventRepository(AuditEventRepositoryContract):
    """In-memory audit store with per-organization integrity chaining.

    Concurrency is serialized with a process-local lock. This does not reproduce
    PostgreSQL advisory/row locks across processes.
    """

    def __init__(self) -> None:
        self._events_by_id: dict[AuditEventId, AuditEvent] = {}
        self._chain_heads: dict[OrganizationId, tuple[AuditEventId, AuditIntegrityHash]] = {}
        self._lock = threading.RLock()
        self._integrity = AuditIntegrityService()

    def add(self, event: AuditEvent) -> None:
        with self._lock:
            chain_org = resolve_audit_chain_organization_id(event)
            previous = self._chain_heads.get(chain_org)
            previous_hash = previous[1] if previous is not None else None
            draft = event.model_copy(
                update={
                    "previous_integrity_hash": None,
                    "integrity_hash": None,
                    "integrity_version": None,
                }
            )
            finalized = self._integrity.finalize_event(draft, previous_hash)
            assert finalized.integrity_hash is not None
            self._events_by_id[finalized.id] = finalized
            self._chain_heads[chain_org] = (finalized.id, finalized.integrity_hash)

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        with self._lock:
            event = self._events_by_id.get(audit_event_id)
            if event is None:
                raise AuditEventNotFound(audit_event_id)
            return event

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        with self._lock:
            events = [
                event
                for event in self._events_by_id.values()
                if _is_in_scope(event, criteria)
            ]

            actions = effective_actions(criteria)
            if actions is not None:
                events = [event for event in events if event.action in actions]
            if criteria.resource_type is not None:
                events = [
                    event
                    for event in events
                    if event.resource_type is criteria.resource_type
                ]
            if criteria.resource_id is not None:
                events = [
                    event for event in events if event.resource_id == criteria.resource_id
                ]
            if criteria.actor_user_id is not None:
                events = [
                    event
                    for event in events
                    if event.actor_user_id == criteria.actor_user_id
                ]
            if criteria.outcome is not None:
                events = [event for event in events if event.outcome is criteria.outcome]
            if criteria.target_organization_id is not None:
                events = [
                    event
                    for event in events
                    if event.target_organization_id == criteria.target_organization_id
                ]
            if criteria.request_id is not None:
                events = [
                    event
                    for event in events
                    if event.metadata.get("request_id") == criteria.request_id
                ]
            if criteria.occurred_from is not None:
                events = [
                    event
                    for event in events
                    if event.occurred_at >= criteria.occurred_from
                ]
            if criteria.occurred_to is not None:
                events = [
                    event for event in events if event.occurred_at < criteria.occurred_to
                ]

            events.sort(
                key=lambda event: (event.occurred_at, event.id.value),
                reverse=not criteria.sort_ascending,
            )
            total = len(events)
            page = events[criteria.offset : criteria.offset + criteria.limit]

            return AuditEventListResult(
                items=tuple(page),
                total=total,
                offset=criteria.offset,
                limit=criteria.limit,
            )

    def get_latest_integrity_hash(
        self,
        organization_id: OrganizationId,
    ) -> AuditIntegrityHash | None:
        head = self.get_chain_head(organization_id)
        return head.latest_integrity_hash if head is not None else None

    def get_chain_head(
        self,
        organization_id: OrganizationId,
    ) -> AuditChainHead | None:
        with self._lock:
            head = self._chain_heads.get(organization_id)
            if head is None:
                return None
            event = self._events_by_id.get(head[0])
            version = (
                event.integrity_version
                if event is not None and event.integrity_version is not None
                else CURRENT_AUDIT_INTEGRITY_VERSION
            )
            return AuditChainHead(
                organization_id=organization_id,
                latest_audit_event_id=head[0],
                latest_integrity_hash=head[1],
                integrity_version=version,
            )
    def list_chain_events(
        self,
        organization_id: OrganizationId,
    ) -> tuple[AuditEvent, ...]:
        with self._lock:
            events = [
                event
                for event in self._events_by_id.values()
                if _belongs_to_chain(event, organization_id)
            ]
            events.sort(key=lambda event: (event.occurred_at, event.id.value))
            return tuple(events)

    def snapshot(self) -> dict[AuditEventId, AuditEvent]:
        """Return a copy of persisted events.

        Chain-head state is derived on restore from integrity fields so callers and
        UnitOfWork rollback remain compatible with the historical flat snapshot shape.
        """

        with self._lock:
            return dict(self._events_by_id)

    def restore(self, snapshot: dict[str, object] | dict[AuditEventId, AuditEvent]) -> None:
        with self._lock:
            if isinstance(snapshot, dict) and "events" in snapshot and "chain_heads" in snapshot:
                events = snapshot["events"]
                heads = snapshot["chain_heads"]
                assert isinstance(events, dict)
                assert isinstance(heads, dict)
                self._events_by_id = dict(events)
                self._chain_heads = dict(heads)
                return
            self._events_by_id = dict(snapshot)  # type: ignore[arg-type]
            self._rebuild_chain_heads_unlocked()

    def _rebuild_chain_heads_unlocked(self) -> None:
        self._chain_heads.clear()
        by_org: dict[OrganizationId, list[AuditEvent]] = {}
        for event in self._events_by_id.values():
            org = resolve_audit_chain_organization_id(event)
            by_org.setdefault(org, []).append(event)
        for org, events in by_org.items():
            events.sort(key=lambda item: (item.occurred_at, item.id.value))
            if not events:
                continue
            last = events[-1]
            if last.integrity_hash is None:
                continue
            self._chain_heads[org] = (last.id, last.integrity_hash)

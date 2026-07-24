from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_chain_head import AuditChainHead
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
)
from backend.core.domain.value_objects.audit_integrity import AuditIntegrityHash


class AuditEventRepositoryContract(Protocol):
    def add(self, event: AuditEvent) -> None:
        ...

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        ...

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        ...

    def get_latest_integrity_hash(
        self,
        organization_id: OrganizationId,
    ) -> AuditIntegrityHash | None:
        ...

    def get_chain_head(
        self,
        organization_id: OrganizationId,
    ) -> AuditChainHead | None:
        ...

    def list_chain_events(
        self,
        organization_id: OrganizationId,
    ) -> tuple[AuditEvent, ...]:
        """Return chain-partition events in ascending integrity order."""
        ...

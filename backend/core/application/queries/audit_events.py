from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


@dataclass(frozen=True, slots=True)
class GetAuditEventQuery:
    audit_event_id: AuditEventId
    scope_organization_id: OrganizationId


@dataclass(frozen=True, slots=True)
class ListAuditEventsQuery:
    scope_organization_id: OrganizationId
    offset: int
    limit: int
    event_name: AuditAction | None = None
    event_category: SecurityEventCategory | None = None
    severity: SecurityEventSignificance | None = None
    action: AuditAction | None = None
    resource_type: AuditResourceType | None = None
    resource_id: UUID | None = None
    actor_user_id: UserId | None = None
    outcome: AuditOutcome | None = None
    target_organization_id: OrganizationId | None = None
    request_id: str | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    sort_ascending: bool = False

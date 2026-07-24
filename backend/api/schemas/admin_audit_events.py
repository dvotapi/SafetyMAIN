from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.api.schemas.knowledge_objects import PaginationResponse


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID | None = None
    authorization_organization_id: UUID | None = None
    target_organization_id: UUID | None = None
    event_name: str
    event_category: str
    severity: str | None = None
    action: str
    resource_type: str
    resource_id: UUID | None = None
    outcome: str
    failure_code: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any]
    occurred_at: datetime
    previous_integrity_hash: str | None = None
    integrity_hash: str | None = None
    integrity_version: int | None = None


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    pagination: PaginationResponse


class AuditChainIntegrityResponse(BaseModel):
    organization_id: UUID
    valid: bool
    checked_event_count: int
    first_invalid_event_id: UUID | None = None
    reason: str | None = None

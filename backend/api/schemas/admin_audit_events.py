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
    action: str
    resource_type: str
    resource_id: UUID | None = None
    outcome: str
    failure_code: str | None = None
    metadata: dict[str, Any]
    occurred_at: datetime


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    pagination: PaginationResponse

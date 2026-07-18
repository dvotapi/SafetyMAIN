from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.value_objects import KnowledgeObjectId


class BaseDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: KnowledgeObjectId
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)

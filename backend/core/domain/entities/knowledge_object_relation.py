from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)


class KnowledgeObjectRelation(BaseModel):
    model_config = ConfigDict(frozen=True)

    relation_id: UUID = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    source_object_id: KnowledgeObjectId = Field(frozen=True)
    target_object_id: KnowledgeObjectId = Field(frozen=True)
    relation_type: KnowledgeObjectRelationType = Field(frozen=True)
    created_at: datetime = Field(frozen=True)

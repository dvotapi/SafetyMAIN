from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from backend.core.domain.value_objects import KnowledgeObjectRelationType


class CreateKnowledgeObjectRelationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_object_id: UUID
    target_object_id: UUID
    type: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        KnowledgeObjectRelationType(value=value)
        return value


class KnowledgeObjectRelationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    organization_id: UUID
    source_object_id: UUID
    target_object_id: UUID
    type: str
    created_at: datetime


class KnowledgeObjectRelationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectRelationResponse, ...] = ()

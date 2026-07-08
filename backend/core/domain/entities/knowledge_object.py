from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectType,
    KnowledgeObjectVersion,
    OrganizationId,
)


class KnowledgeObjectStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class KnowledgeObjectHeader(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: KnowledgeObjectId = Field(frozen=True)
    object_type: KnowledgeObjectType = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    status: KnowledgeObjectStatus
    version: KnowledgeObjectVersion
    created_at: datetime = Field(frozen=True)
    updated_at: datetime


class KnowledgeObject(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    header: KnowledgeObjectHeader
    payload: dict[str, Any] = Field(default_factory=dict)

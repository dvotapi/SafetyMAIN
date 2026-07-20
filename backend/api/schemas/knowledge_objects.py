from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import KnowledgeObjectType


class CreateKnowledgeObjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        KnowledgeObjectType(value=value)
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("Metadata must be a JSON object.")
        return value


class UpdateKnowledgeObjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("Metadata must be a JSON object.")
        return value


class KnowledgeObjectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    organization_id: UUID
    type: str
    status: str
    version: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class KnowledgeObjectHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectResponse, ...] = ()


class KnowledgeObjectListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectResponse, ...] = ()


class PaginationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    offset: int
    limit: int
    total: int


class KnowledgeObjectSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[KnowledgeObjectResponse, ...] = ()
    pagination: PaginationResponse

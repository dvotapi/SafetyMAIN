from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class UpdateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationListResponse(BaseModel):
    items: list[OrganizationResponse]
    pagination: PaginationResponse

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.api.schemas.knowledge_objects import PaginationResponse

MembershipRoleValue = Literal["admin", "member", "auditor"]


class CreateMembershipRequest(BaseModel):
    user_id: UUID
    organization_id: UUID
    role: MembershipRoleValue
    is_active: bool = True


class UpdateMembershipRoleRequest(BaseModel):
    role: MembershipRoleValue


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MembershipListResponse(BaseModel):
    items: list[MembershipResponse]
    pagination: PaginationResponse

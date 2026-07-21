from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.api.schemas.knowledge_objects import PaginationResponse

InvitationRoleValue = Literal["admin", "member", "auditor"]
InvitationStatusValue = Literal["PENDING", "ACCEPTED", "REVOKED", "EXPIRED"]


class CreateInvitationRequest(BaseModel):
    organization_id: UUID
    email: str = Field(min_length=1, max_length=320)
    role: InvitationRoleValue
    expires_at: datetime | None = None


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1)


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: str
    role: str
    status: InvitationStatusValue
    expires_at: datetime
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None


class CreateInvitationResponse(BaseModel):
    invitation: InvitationResponse
    token: str


class ReissueInvitationResponse(BaseModel):
    invitation: InvitationResponse
    token: str


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    pagination: PaginationResponse

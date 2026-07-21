from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import InvitationId, OrganizationId, Role, UserId


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


DEFAULT_INVITATION_TTL_DAYS = 7


class Invitation(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: InvitationId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    email: str
    role: Role
    status: InvitationStatus
    token_hash: str
    expires_at: datetime
    created_by: UserId = Field(frozen=True)
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if not normalized_value:
            raise ValueError("Invitation email must not be empty.")
        return normalized_value

    def effective_status(self, *, now: datetime) -> InvitationStatus:
        if self.status is InvitationStatus.ACCEPTED:
            return InvitationStatus.ACCEPTED
        if self.status is InvitationStatus.REVOKED:
            return InvitationStatus.REVOKED
        if now >= self.expires_at:
            return InvitationStatus.EXPIRED
        return InvitationStatus.PENDING

    def is_acceptable(self, *, now: datetime) -> bool:
        return self.effective_status(now=now) is InvitationStatus.PENDING

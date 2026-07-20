from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    REVOKED = "REVOKED"


class Membership(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: MembershipId = Field(frozen=True)
    user_id: UserId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    status: MembershipStatus
    role: Role
    joined_at: datetime | None = Field(default=None, frozen=True)
    revoked_at: datetime | None = None

    def is_active(self) -> bool:
        return self.status is MembershipStatus.ACTIVE

    def grants_organization_access(self) -> bool:
        return self.is_active()

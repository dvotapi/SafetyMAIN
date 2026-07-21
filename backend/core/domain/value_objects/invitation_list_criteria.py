from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.domain.entities.invitation import Invitation, InvitationStatus
from backend.core.domain.value_objects import OrganizationId, Role


@dataclass(frozen=True, slots=True)
class InvitationListCriteria:
    organization_id: OrganizationId
    offset: int
    limit: int
    as_of: datetime
    email: str | None = None
    role: Role | None = None
    status: InvitationStatus | None = None
    sort_ascending: bool = False


@dataclass(frozen=True, slots=True)
class InvitationListResult:
    items: tuple[Invitation, ...]
    total: int
    offset: int
    limit: int

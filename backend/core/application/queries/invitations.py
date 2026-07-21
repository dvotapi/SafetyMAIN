from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.invitation import InvitationStatus
from backend.core.domain.value_objects import InvitationId, OrganizationId, Role


@dataclass(frozen=True, slots=True)
class GetInvitationQuery:
    invitation_id: InvitationId


@dataclass(frozen=True, slots=True)
class ListInvitationsQuery:
    organization_id: OrganizationId
    offset: int
    limit: int
    email: str | None = None
    role: Role | None = None
    status: InvitationStatus | None = None
    sort_ascending: bool = False

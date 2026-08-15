from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.membership import MembershipStatus
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.role import Role


@dataclass(frozen=True, slots=True)
class GetAuthSessionQuery:
    user_id: UserId


@dataclass(frozen=True, slots=True)
class AuthSessionMembership:
    organization_id: OrganizationId
    organization_name: str
    role: Role
    status: MembershipStatus
    permissions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthSession:
    user_id: UserId
    email: str
    display_name: str
    status: str
    memberships: tuple[AuthSessionMembership, ...]

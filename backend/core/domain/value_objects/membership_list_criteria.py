from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import OrganizationId, Role, UserId


@dataclass(frozen=True, slots=True)
class MembershipListCriteria:
    organization_id: OrganizationId
    offset: int
    limit: int
    user_id: UserId | None = None
    role: Role | None = None
    is_active: bool | None = None
    sort_ascending: bool = False


@dataclass(frozen=True, slots=True)
class MembershipListResult:
    items: tuple[Membership, ...]
    total: int
    offset: int
    limit: int

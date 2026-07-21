from __future__ import annotations

from dataclasses import dataclass

from backend.core.domain.value_objects import OrganizationId, Role, UserId


@dataclass(frozen=True, slots=True)
class ListMembershipsQuery:
    organization_id: OrganizationId
    offset: int
    limit: int
    user_id: UserId | None = None
    role: Role | None = None
    is_active: bool | None = None
    sort_ascending: bool = False

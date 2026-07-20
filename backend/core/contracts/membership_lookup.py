from __future__ import annotations

from typing import Protocol, Sequence

from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import OrganizationId, UserId


class MembershipLookupPort(Protocol):
    """Application port for resolving organization memberships."""

    def get_membership(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        ...

    def list_memberships_for_user(self, user_id: UserId) -> Sequence[Membership]:
        ...

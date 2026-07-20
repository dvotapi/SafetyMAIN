from __future__ import annotations

from typing import Protocol, Sequence

from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId


class MembershipRepositoryContract(Protocol):
    """Repository contract for organization memberships."""

    def add(self, membership: Membership) -> None:
        ...

    def get(self, membership_id: MembershipId) -> Membership:
        ...

    def get_by_user_and_organization(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        ...

    def list_by_user(self, user_id: UserId) -> Sequence[Membership]:
        ...

    def list_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> Sequence[Membership]:
        ...

    def save(self, membership: Membership) -> None:
        ...

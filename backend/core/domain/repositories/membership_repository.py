from __future__ import annotations

from typing import Protocol, Sequence

from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId
from backend.core.domain.value_objects.membership_list_criteria import (
    MembershipListCriteria,
    MembershipListResult,
)


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

    def list_memberships(self, criteria: MembershipListCriteria) -> MembershipListResult:
        ...

    def save(self, membership: Membership) -> None:
        ...

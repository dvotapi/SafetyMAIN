from __future__ import annotations

from typing import Sequence

from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId


class InMemoryMembershipStore(MembershipLookupPort, MembershipVerificationPort):
    """In-memory membership adapter for development and tests."""

    def __init__(self) -> None:
        self._memberships_by_id: dict[MembershipId, Membership] = {}
        self._memberships_by_user_and_org: dict[tuple[UserId, OrganizationId], MembershipId] = (
            {}
        )

    def register_membership(self, membership: Membership) -> None:
        self._memberships_by_id[membership.id] = membership
        self._memberships_by_user_and_org[(membership.user_id, membership.organization_id)] = (
            membership.id
        )

    def get_membership(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        membership_id = self._memberships_by_user_and_org.get((user_id, organization_id))
        if membership_id is None:
            return None
        return self._memberships_by_id.get(membership_id)

    def list_memberships_for_user(self, user_id: UserId) -> Sequence[Membership]:
        return tuple(
            membership
            for membership in self._memberships_by_id.values()
            if membership.user_id == user_id
        )

    def is_active_member(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> bool:
        membership = self.get_membership(user_id, organization_id)
        if membership is None:
            return False
        return membership.grants_organization_access()

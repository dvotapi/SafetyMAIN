from __future__ import annotations

from backend.core.domain.entities.membership import Membership
from backend.core.domain.exceptions import MembershipNotFound
from backend.core.domain.repositories import MembershipRepositoryContract
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId


class InMemoryMembershipRepository(MembershipRepositoryContract):
    def __init__(self) -> None:
        self._memberships_by_id: dict[MembershipId, Membership] = {}
        self._memberships_by_user_and_org: dict[tuple[UserId, OrganizationId], MembershipId] = (
            {}
        )

    def add(self, membership: Membership) -> None:
        self._memberships_by_id[membership.id] = membership
        self._memberships_by_user_and_org[(membership.user_id, membership.organization_id)] = (
            membership.id
        )

    def get(self, membership_id: MembershipId) -> Membership:
        membership = self._memberships_by_id.get(membership_id)
        if membership is None:
            raise MembershipNotFound(
                user_id=UserId(value=membership_id.value),
                organization_id=OrganizationId(value=membership_id.value),
            )
        return membership

    def get_by_user_and_organization(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        membership_id = self._memberships_by_user_and_org.get((user_id, organization_id))
        if membership_id is None:
            return None
        return self._memberships_by_id.get(membership_id)

    def list_by_user(self, user_id: UserId) -> tuple[Membership, ...]:
        return tuple(
            membership
            for membership in self._memberships_by_id.values()
            if membership.user_id == user_id
        )

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Membership, ...]:
        return tuple(
            membership
            for membership in self._memberships_by_id.values()
            if membership.organization_id == organization_id
        )

    def save(self, membership: Membership) -> None:
        if membership.id not in self._memberships_by_id:
            raise MembershipNotFound(
                user_id=membership.user_id,
                organization_id=membership.organization_id,
            )
        self._memberships_by_id[membership.id] = membership

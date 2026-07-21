from __future__ import annotations

from backend.core.domain.entities.membership import Membership
from backend.core.domain.exceptions import MembershipByIdNotFound, MembershipNotFound
from backend.core.domain.repositories import MembershipRepositoryContract
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId
from backend.core.domain.value_objects.membership_list_criteria import (
    MembershipListCriteria,
    MembershipListResult,
)


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
            raise MembershipByIdNotFound(membership_id)
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

    def list_memberships(self, criteria: MembershipListCriteria) -> MembershipListResult:
        memberships = [
            membership
            for membership in self._memberships_by_id.values()
            if membership.organization_id == criteria.organization_id
        ]

        if criteria.user_id is not None:
            memberships = [
                membership
                for membership in memberships
                if membership.user_id == criteria.user_id
            ]
        if criteria.role is not None:
            memberships = [
                membership
                for membership in memberships
                if membership.role.value == criteria.role.value
            ]
        if criteria.is_active is not None:
            memberships = [
                membership
                for membership in memberships
                if membership.is_active() == criteria.is_active
            ]

        memberships.sort(key=lambda membership: membership.id.value)
        memberships.sort(
            key=lambda membership: membership.joined_at or membership.updated_at,
            reverse=not criteria.sort_ascending,
        )
        total = len(memberships)
        page = memberships[criteria.offset : criteria.offset + criteria.limit]

        return MembershipListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def save(self, membership: Membership) -> None:
        if membership.id not in self._memberships_by_id:
            raise MembershipNotFound(
                user_id=membership.user_id,
                organization_id=membership.organization_id,
            )
        self._memberships_by_id[membership.id] = membership

    def snapshot(
        self,
    ) -> tuple[
        dict[MembershipId, Membership],
        dict[tuple[UserId, OrganizationId], MembershipId],
    ]:
        return (
            dict(self._memberships_by_id),
            dict(self._memberships_by_user_and_org),
        )

    def restore(
        self,
        snapshot: tuple[
            dict[MembershipId, Membership],
            dict[tuple[UserId, OrganizationId], MembershipId],
        ],
    ) -> None:
        memberships_by_id, memberships_by_user_and_org = snapshot
        self._memberships_by_id = dict(memberships_by_id)
        self._memberships_by_user_and_org = dict(memberships_by_user_and_org)

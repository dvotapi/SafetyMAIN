from __future__ import annotations

from datetime import UTC, datetime

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.exceptions import (
    CannotActivateRevokedMembership,
    InactiveMembership,
    MembershipAlreadyActive,
    MembershipAlreadyRevoked,
)


class MembershipService:
    def activate(self, membership: Membership) -> Membership:
        if membership.status is MembershipStatus.ACTIVE:
            raise MembershipAlreadyActive(membership.id)

        if membership.status is MembershipStatus.REVOKED:
            raise CannotActivateRevokedMembership(membership.id)

        return membership.model_copy(
            update={
                "status": MembershipStatus.ACTIVE,
                "joined_at": membership.joined_at or datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def revoke(self, membership: Membership) -> Membership:
        if membership.status is MembershipStatus.REVOKED:
            raise MembershipAlreadyRevoked(membership.id)

        return membership.model_copy(
            update={
                "status": MembershipStatus.REVOKED,
                "revoked_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def ensure_grants_organization_access(self, membership: Membership) -> None:
        if not membership.grants_organization_access():
            raise InactiveMembership(membership.id)

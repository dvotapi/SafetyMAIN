from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_membership_store import (
    InMemoryMembershipStore,
)


def test_in_memory_membership_store_tracks_active_membership() -> None:
    store = InMemoryMembershipStore()
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=user_id,
        organization_id=organization_id,
        status=MembershipStatus.ACTIVE,
        role=Role.member(),
        joined_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    store.register_membership(membership)

    assert store.is_active_member(user_id, organization_id) is True
    assert store.get_membership(user_id, organization_id) == membership
    assert store.list_memberships_for_user(user_id) == (membership,)


def test_in_memory_membership_store_rejects_invited_membership() -> None:
    store = InMemoryMembershipStore()
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            status=MembershipStatus.INVITED,
            role=Role.member(),
            updated_at=datetime.now(UTC),
        )
    )

    assert store.is_active_member(user_id, organization_id) is False

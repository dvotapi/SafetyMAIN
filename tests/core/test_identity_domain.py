from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities import Membership, MembershipStatus
from backend.core.domain.exceptions import (
    CannotActivateRevokedMembership,
    InactiveMembership,
    MembershipAlreadyActive,
    MembershipAlreadyRevoked,
    MembershipNotFound,
    SafetyMainDomainError,
    UserNotFound,
)
from backend.core.domain.services import MembershipService
from backend.core.domain.value_objects import (
    MembershipId,
    OrganizationId,
    Role,
    UserId,
)


def test_user_not_found_is_domain_error() -> None:
    user_id = UserId(value=uuid4())

    error = UserNotFound(user_id)

    assert isinstance(error, SafetyMainDomainError)
    assert error.user_id == user_id


def test_membership_not_found_carries_user_and_organization_context() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())

    error = MembershipNotFound(user_id=user_id, organization_id=organization_id)

    assert error.user_id == user_id
    assert error.organization_id == organization_id


def test_membership_service_activates_invited_membership() -> None:
    service = MembershipService()
    now = datetime.now(UTC)
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.INVITED,
        role=Role.member(),
        updated_at=now,
    )

    activated = service.activate(membership)

    assert activated.status is MembershipStatus.ACTIVE
    assert activated.joined_at is not None


def test_membership_service_rejects_reactivating_revoked_membership() -> None:
    service = MembershipService()
    now = datetime.now(UTC)
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.REVOKED,
        role=Role.member(),
        updated_at=now,
        revoked_at=now,
    )

    with pytest.raises(CannotActivateRevokedMembership):
        service.activate(membership)


def test_membership_service_revoke_is_idempotent_guarded() -> None:
    service = MembershipService()
    now = datetime.now(UTC)
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.REVOKED,
        role=Role.member(),
        updated_at=now,
        revoked_at=now,
    )

    with pytest.raises(MembershipAlreadyRevoked):
        service.revoke(membership)


def test_membership_service_raises_when_access_is_not_granted() -> None:
    service = MembershipService()
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.INVITED,
        role=Role.member(),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(InactiveMembership):
        service.ensure_grants_organization_access(membership)


def test_membership_service_rejects_double_activation() -> None:
    service = MembershipService()
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.ACTIVE,
        role=Role.member(),
        joined_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    with pytest.raises(MembershipAlreadyActive):
        service.activate(membership)

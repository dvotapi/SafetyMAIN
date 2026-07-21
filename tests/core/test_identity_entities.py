from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.entities import (
    Membership,
    MembershipStatus,
    Organization,
    OrganizationStatus,
    User,
    UserStatus,
)
from backend.core.domain.value_objects import (
    MembershipId,
    OrganizationId,
    Role,
    UserId,
)


def test_user_normalizes_email_and_display_name() -> None:
    user = User(
        id=UserId(value=uuid4()),
        display_name="  Safety Operator  ",
        email="  Operator@Example.com ",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert user.display_name == "Safety Operator"
    assert user.email == "operator@example.com"
    assert user.can_authenticate() is True


def test_user_rejects_empty_email() -> None:
    with pytest.raises(ValidationError):
        User(
            id=UserId(value=uuid4()),
            display_name="Operator",
            email="   ",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_suspended_user_cannot_authenticate() -> None:
    user = User(
        id=UserId(value=uuid4()),
        display_name="Operator",
        email="operator@example.com",
        status=UserStatus.SUSPENDED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert user.can_authenticate() is False


def test_organization_normalizes_name() -> None:
    now = datetime.now(UTC)
    organization = Organization(
        id=OrganizationId(value=uuid4()),
        name="  SafetyMAIN  ",
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )

    assert organization.name == "SafetyMAIN"


def test_active_membership_grants_organization_access() -> None:
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.ACTIVE,
        role=Role.member(),
        joined_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert membership.grants_organization_access() is True


def test_invited_membership_does_not_grant_organization_access() -> None:
    membership = Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.INVITED,
        role=Role.member(),
        updated_at=datetime.now(UTC),
    )

    assert membership.grants_organization_access() is False

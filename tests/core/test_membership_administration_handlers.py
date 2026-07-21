from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.application.commands.membership_lifecycle import (
    ActivateMembershipCommand,
    DeactivateMembershipCommand,
)
from backend.core.application.commands.update_membership_role import UpdateMembershipRoleCommand
from backend.core.application.handlers.create_membership import CreateMembershipHandler
from backend.core.application.handlers.membership_lifecycle import (
    ActivateMembershipHandler,
    DeactivateMembershipHandler,
)
from backend.core.application.handlers.update_membership_role import UpdateMembershipRoleHandler
from backend.core.application.policies.membership_administration import (
    MembershipAuthorizationContext,
)
from backend.core.domain.entities.membership import MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import (
    DuplicateMembership,
    InvalidMembershipRole,
    LastOrganizationAdministratorError,
    SelfMembershipDeactivationError,
    SelfMembershipRoleDowngradeError,
)
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def _seed_user(uow: InMemoryUnitOfWork) -> User:
    now = datetime.now(UTC)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email=f"operator-{uuid4()}@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    uow.users.add(user)
    return user


def _seed_organization(uow: InMemoryUnitOfWork) -> Organization:
    now = datetime.now(UTC)
    organization = Organization(
        id=OrganizationId(value=uuid4()),
        name="Target Organization",
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    uow.organizations.add(organization)
    return organization


def _authorization_for(
    uow: InMemoryUnitOfWork,
    *,
    user: User,
    organization: Organization,
) -> MembershipAuthorizationContext:
    membership = uow.memberships.get_by_user_and_organization(user.id, organization.id)
    assert membership is not None
    return MembershipAuthorizationContext(
        actor_user_id=user.id,
        authorization_organization_id=organization.id,
        authorization_membership_id=membership.id,
    )


def test_create_membership_persists_membership() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)

    membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.member(),
        )
    )

    assert membership.role.value == "member"
    assert membership.is_active() is True
    assert uow.committed is True


def test_create_membership_rejects_duplicate() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)
    handler = CreateMembershipHandler(uow)
    handler.handle(
        CreateMembershipCommand(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.member(),
        )
    )

    with pytest.raises(DuplicateMembership):
        handler.handle(
            CreateMembershipCommand(
                user_id=user.id,
                organization_id=organization.id,
                role=Role.auditor(),
            )
        )


def test_create_membership_rejects_invalid_role() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)

    with pytest.raises(InvalidMembershipRole):
        CreateMembershipHandler(uow).handle(
            CreateMembershipCommand(
                user_id=user.id,
                organization_id=organization.id,
                role=Role(value="owner"),
            )
        )


def test_deactivate_membership_rejects_self_deactivation() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)
    membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.admin(),
        )
    )

    with pytest.raises(SelfMembershipDeactivationError):
        DeactivateMembershipHandler(uow).handle(
            DeactivateMembershipCommand(
                membership_id=membership.id,
                authorization=_authorization_for(uow, user=user, organization=organization),
            )
        )


def test_role_change_rejects_self_admin_downgrade() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)
    membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.admin(),
        )
    )

    with pytest.raises(SelfMembershipRoleDowngradeError):
        UpdateMembershipRoleHandler(uow).handle(
            UpdateMembershipRoleCommand(
                membership_id=membership.id,
                role=Role.member(),
                authorization=_authorization_for(uow, user=user, organization=organization),
            )
        )


def test_deactivate_last_administrator_is_rejected() -> None:
    uow = InMemoryUnitOfWork()
    admin_user = _seed_user(uow)
    actor = _seed_user(uow)
    organization = _seed_organization(uow)
    admin_membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=admin_user.id,
            organization_id=organization.id,
            role=Role.admin(),
        )
    )
    CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=actor.id,
            organization_id=organization.id,
            role=Role.member(),
        )
    )

    with pytest.raises(LastOrganizationAdministratorError):
        DeactivateMembershipHandler(uow).handle(
            DeactivateMembershipCommand(
                membership_id=admin_membership.id,
                authorization=_authorization_for(uow, user=actor, organization=organization),
            )
        )


def test_activate_and_deactivate_membership() -> None:
    uow = InMemoryUnitOfWork()
    user = _seed_user(uow)
    organization = _seed_organization(uow)
    actor = _seed_user(uow)
    CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=actor.id,
            organization_id=organization.id,
            role=Role.admin(),
        )
    )
    membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=user.id,
            organization_id=organization.id,
            role=Role.member(),
            is_active=False,
        )
    )
    assert membership.status is MembershipStatus.REVOKED

    activated = ActivateMembershipHandler(uow).handle(
        ActivateMembershipCommand(membership_id=membership.id)
    )
    assert activated.is_active() is True

    deactivated = DeactivateMembershipHandler(uow).handle(
        DeactivateMembershipCommand(
            membership_id=activated.id,
            authorization=_authorization_for(uow, user=actor, organization=organization),
        )
    )
    assert deactivated.is_active() is False

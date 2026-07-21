from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.application.commands.invitation_lifecycle import (
    AcceptInvitationCommand,
    CreateInvitationCommand,
    ReissueInvitationCommand,
    RevokeInvitationCommand,
)
from backend.core.application.handlers.create_invitation import CreateInvitationHandler
from backend.core.application.handlers.invitation_lifecycle import (
    AcceptInvitationHandler,
    ReissueInvitationHandler,
    RevokeInvitationHandler,
)
from backend.core.application.handlers.create_membership import CreateMembershipHandler
from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.domain.entities.invitation import InvitationStatus
from backend.core.domain.entities.membership import MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions.invitation import (
    DuplicateActiveInvitation,
    ExistingActiveMembership,
    InvitationAlreadyAccepted,
    InvitationAlreadyRevoked,
    InvitationEmailMismatch,
    InvitationExpired,
    InvitationTokenInvalid,
)
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.domain.value_objects.invitation_token import hash_invitation_token
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta


def _seed_user(uow: InMemoryUnitOfWork, *, email: str | None = None) -> User:
    now = datetime.now(UTC)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email=email or f"operator-{uuid4()}@example.com",
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


def test_create_invitation_returns_token_and_normalizes_email() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))

    result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email="  Invitee@Example.com ",
            role=Role.member(),
            created_by=creator.id,
        )
    )

    assert result.token
    assert result.invitation.email == "invitee@example.com"
    assert result.invitation.token_hash == hash_invitation_token(result.token)
    assert uow.committed is True


def test_create_invitation_rejects_duplicate_active_invitation() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    handler = CreateInvitationHandler(uow, clock)
    handler.handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email="invitee@example.com",
            role=Role.member(),
            created_by=creator.id,
        )
    )

    with pytest.raises(DuplicateActiveInvitation):
        handler.handle(
            CreateInvitationCommand(
                organization_id=organization.id,
                email="invitee@example.com",
                role=Role.auditor(),
                created_by=creator.id,
            )
        )


def test_create_invitation_rejects_existing_active_membership() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=invitee.id,
            organization_id=organization.id,
            role=Role.member(),
        )
    )

    with pytest.raises(ExistingActiveMembership):
        CreateInvitationHandler(uow, FixedClock(datetime.now(UTC))).handle(
            CreateInvitationCommand(
                organization_id=organization.id,
                email=invitee.email,
                role=Role.member(),
                created_by=creator.id,
            )
        )


def test_accept_invitation_creates_membership() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.auditor(),
            created_by=creator.id,
        )
    )

    accepted = AcceptInvitationHandler(uow, clock).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
        )
    )

    membership = uow.memberships.get_by_user_and_organization(invitee.id, organization.id)
    assert accepted.status is InvitationStatus.ACCEPTED
    assert membership is not None
    assert membership.is_active() is True
    assert membership.role.value == "auditor"


def test_accept_invitation_reactivates_inactive_membership() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    membership = CreateMembershipHandler(uow).handle(
        CreateMembershipCommand(
            user_id=invitee.id,
            organization_id=organization.id,
            role=Role.member(),
            is_active=False,
        )
    )
    assert membership.status is MembershipStatus.REVOKED

    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.admin(),
            created_by=creator.id,
        )
    )
    AcceptInvitationHandler(uow, clock).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
        )
    )

    updated = uow.memberships.get_by_user_and_organization(invitee.id, organization.id)
    assert updated is not None
    assert updated.is_active() is True
    assert updated.role.value == "admin"


def test_accept_invitation_rejects_email_mismatch() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    other_user = _seed_user(uow, email="other@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
        )
    )

    with pytest.raises(InvitationEmailMismatch):
        AcceptInvitationHandler(uow, clock).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=other_user.id,
            )
        )


def test_accept_invitation_rejects_expired_invitation() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
        )
    )
    clock.advance(timedelta(days=8))

    with pytest.raises(InvitationExpired):
        AcceptInvitationHandler(uow, clock).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
            )
        )


def test_reissue_invalidates_old_token() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
        )
    )
    reissue_result = ReissueInvitationHandler(uow, clock).handle(
        ReissueInvitationCommand(invitation_id=create_result.invitation.id)
    )

    with pytest.raises(InvitationTokenInvalid):
        AcceptInvitationHandler(uow, clock).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
            )
        )

    accepted = AcceptInvitationHandler(uow, clock).handle(
        AcceptInvitationCommand(
            token=reissue_result.token,
            accepting_user_id=invitee.id,
        )
    )
    assert accepted.status is InvitationStatus.ACCEPTED


def test_accept_invitation_is_single_use() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
        )
    )
    AcceptInvitationHandler(uow, clock).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
        )
    )

    with pytest.raises(InvitationAlreadyAccepted):
        AcceptInvitationHandler(uow, clock).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
            )
        )


def test_revoke_invitation_blocks_acceptance() -> None:
    uow = InMemoryUnitOfWork()
    creator = _seed_user(uow)
    invitee = _seed_user(uow, email="invitee@example.com")
    organization = _seed_organization(uow)
    clock = FixedClock(datetime.now(UTC))
    create_result = CreateInvitationHandler(uow, clock).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
        )
    )
    RevokeInvitationHandler(uow, clock).handle(
        RevokeInvitationCommand(invitation_id=create_result.invitation.id)
    )

    with pytest.raises(InvitationAlreadyRevoked):
        AcceptInvitationHandler(uow, clock).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
            )
        )

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.commands.create_membership import CreateMembershipCommand
from backend.core.application.commands.invitation_lifecycle import (
    AcceptInvitationCommand,
    CreateInvitationCommand,
    ReissueInvitationCommand,
    RevokeInvitationCommand,
)
from backend.core.application.handlers.create_invitation import CreateInvitationHandler
from backend.core.application.handlers.create_membership import CreateMembershipHandler
from backend.core.application.handlers.invitation_lifecycle import (
    AcceptInvitationHandler,
    ReissueInvitationHandler,
    RevokeInvitationHandler,
)
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
from tests.core.audit_test_support import authenticated_audit_context, make_admin_audit_stack


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


def _admin_context(*, actor: UserId, organization: OrganizationId) -> AuditContext:
    return AuditContext(
        actor_user_id=actor,
        authorization_organization_id=organization,
    )


def _invitation_stack(clock: FixedClock | None = None):
    resolved_clock = clock or FixedClock(datetime.now(UTC))
    stack = make_admin_audit_stack(clock=resolved_clock)
    return stack, resolved_clock


def test_create_invitation_returns_token_and_normalizes_email() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)

    result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email="  Invitee@Example.com ",
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )

    assert result.token
    assert result.invitation.email == "invitee@example.com"
    assert result.invitation.token_hash == hash_invitation_token(result.token)
    assert stack.uow.committed is True


def test_create_invitation_rejects_duplicate_active_invitation() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    handler = CreateInvitationHandler(stack.uow, clock, stack.audit)
    handler.handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email="invitee@example.com",
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )

    with pytest.raises(DuplicateActiveInvitation):
        handler.handle(
            CreateInvitationCommand(
                organization_id=organization.id,
                email="invitee@example.com",
                role=Role.auditor(),
                created_by=creator.id,
                audit_context=ctx,
            )
        )


def test_create_invitation_rejects_existing_active_membership() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    CreateMembershipHandler(stack.uow, stack.audit).handle(
        CreateMembershipCommand(
            user_id=invitee.id,
            organization_id=organization.id,
            role=Role.member(),
            audit_context=ctx,
        )
    )

    with pytest.raises(ExistingActiveMembership):
        CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
            CreateInvitationCommand(
                organization_id=organization.id,
                email=invitee.email,
                role=Role.member(),
                created_by=creator.id,
                audit_context=ctx,
            )
        )


def test_accept_invitation_creates_membership() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.auditor(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )

    accepted = AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
            audit_context=authenticated_audit_context(invitee.id),
        )
    )

    membership = stack.uow.memberships.get_by_user_and_organization(invitee.id, organization.id)
    assert accepted.status is InvitationStatus.ACCEPTED
    assert membership is not None
    assert membership.is_active() is True
    assert membership.role.value == "auditor"


def test_accept_invitation_reactivates_inactive_membership() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    membership = CreateMembershipHandler(stack.uow, stack.audit).handle(
        CreateMembershipCommand(
            user_id=invitee.id,
            organization_id=organization.id,
            role=Role.member(),
            is_active=False,
            audit_context=ctx,
        )
    )
    assert membership.status is MembershipStatus.REVOKED

    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.admin(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )
    AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
            audit_context=authenticated_audit_context(invitee.id),
        )
    )

    updated = stack.uow.memberships.get_by_user_and_organization(invitee.id, organization.id)
    assert updated is not None
    assert updated.is_active() is True
    assert updated.role.value == "admin"


def test_accept_invitation_rejects_email_mismatch() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    other_user = _seed_user(stack.uow, email="other@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )

    with pytest.raises(InvitationEmailMismatch):
        AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=other_user.id,
                audit_context=authenticated_audit_context(other_user.id),
            )
        )


def test_accept_invitation_rejects_expired_invitation() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )
    clock.advance(timedelta(days=8))

    with pytest.raises(InvitationExpired):
        AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
                audit_context=authenticated_audit_context(invitee.id),
            )
        )


def test_reissue_invalidates_old_token() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )
    reissue_result = ReissueInvitationHandler(stack.uow, clock, stack.audit).handle(
        ReissueInvitationCommand(
            invitation_id=create_result.invitation.id,
            audit_context=ctx,
        )
    )

    with pytest.raises(InvitationTokenInvalid):
        AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
                audit_context=authenticated_audit_context(invitee.id),
            )
        )

    accepted = AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
        AcceptInvitationCommand(
            token=reissue_result.token,
            accepting_user_id=invitee.id,
            audit_context=authenticated_audit_context(invitee.id),
        )
    )
    assert accepted.status is InvitationStatus.ACCEPTED


def test_accept_invitation_is_single_use() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )
    AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
        AcceptInvitationCommand(
            token=create_result.token,
            accepting_user_id=invitee.id,
            audit_context=authenticated_audit_context(invitee.id),
        )
    )

    with pytest.raises(InvitationAlreadyAccepted):
        AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
                audit_context=authenticated_audit_context(invitee.id),
            )
        )


def test_revoke_invitation_blocks_acceptance() -> None:
    stack, clock = _invitation_stack()
    creator = _seed_user(stack.uow)
    invitee = _seed_user(stack.uow, email="invitee@example.com")
    organization = _seed_organization(stack.uow)
    ctx = _admin_context(actor=creator.id, organization=organization.id)
    create_result = CreateInvitationHandler(stack.uow, clock, stack.audit).handle(
        CreateInvitationCommand(
            organization_id=organization.id,
            email=invitee.email,
            role=Role.member(),
            created_by=creator.id,
            audit_context=ctx,
        )
    )
    RevokeInvitationHandler(stack.uow, clock, stack.audit).handle(
        RevokeInvitationCommand(
            invitation_id=create_result.invitation.id,
            audit_context=ctx,
        )
    )

    with pytest.raises(InvitationAlreadyRevoked):
        AcceptInvitationHandler(stack.uow, clock, stack.audit).handle(
            AcceptInvitationCommand(
                token=create_result.token,
                accepting_user_id=invitee.id,
                audit_context=authenticated_audit_context(invitee.id),
            )
        )

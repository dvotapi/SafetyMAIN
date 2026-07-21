from __future__ import annotations

from uuid import uuid4

from backend.core.application.commands.invitation_lifecycle import CreateInvitationCommand
from backend.core.application.policies.membership_administration import validate_membership_role
from backend.core.application.results.invitation_results import InvitationWithTokenResult
from backend.core.application.services.invitation_membership_provisioning import (
    default_invitation_expiration,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.invitation import (
    DEFAULT_INVITATION_TTL_DAYS,
    Invitation,
    InvitationStatus,
)
from backend.core.domain.exceptions import OrganizationAlreadyInactive
from backend.core.domain.exceptions.invitation import (
    DuplicateActiveInvitation,
    ExistingActiveMembership,
)
from backend.core.domain.value_objects import InvitationId
from backend.core.domain.value_objects.invitation_token import generate_invitation_token


class CreateInvitationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, command: CreateInvitationCommand) -> InvitationWithTokenResult:
        validate_membership_role(command.role)

        organization = self._unit_of_work.organizations.get(command.organization_id)
        if not organization.is_active():
            raise OrganizationAlreadyInactive(organization.id)

        normalized_email = command.email.strip().lower()
        now = self._clock.now()
        expires_at = command.expires_at or default_invitation_expiration(
            now=now,
            ttl_days=DEFAULT_INVITATION_TTL_DAYS,
        )
        if expires_at <= now:
            raise ValueError("Invitation expiration must be in the future.")

        existing_invitation = (
            self._unit_of_work.invitations.get_active_pending_by_organization_and_email(
                command.organization_id,
                normalized_email,
            )
        )
        if existing_invitation is not None and existing_invitation.is_acceptable(now=now):
            raise DuplicateActiveInvitation(
                organization_id=command.organization_id,
                email=normalized_email,
            )

        existing_user = self._unit_of_work.users.get_by_email(normalized_email)
        if existing_user is not None:
            existing_membership = self._unit_of_work.memberships.get_by_user_and_organization(
                existing_user.id,
                command.organization_id,
            )
            if existing_membership is not None and existing_membership.is_active():
                raise ExistingActiveMembership(
                    user_id=existing_user.id,
                    organization_id=command.organization_id,
                )

        token, token_hash = generate_invitation_token()
        invitation = Invitation(
            id=InvitationId(value=uuid4()),
            organization_id=command.organization_id,
            email=normalized_email,
            role=command.role,
            status=InvitationStatus.PENDING,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=command.created_by,
            created_at=now,
            updated_at=now,
        )
        self._unit_of_work.invitations.add(invitation)
        self._unit_of_work.commit()
        return InvitationWithTokenResult(invitation=invitation, token=token)

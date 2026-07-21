from __future__ import annotations

from backend.core.application.commands.invitation_lifecycle import (
    AcceptInvitationCommand,
    ReissueInvitationCommand,
    RevokeInvitationCommand,
)
from backend.core.application.results.invitation_results import InvitationWithTokenResult
from backend.core.application.services.invitation_membership_provisioning import (
    default_invitation_expiration,
    provision_membership_for_invitation,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.invitation import (
    DEFAULT_INVITATION_TTL_DAYS,
    Invitation,
    InvitationStatus,
)
from backend.core.domain.exceptions import UserAlreadyDeactivated
from backend.core.domain.exceptions.invitation import (
    InvitationAlreadyAccepted,
    InvitationAlreadyRevoked,
    InvitationEmailMismatch,
    InvitationExpired,
    InvitationTokenInvalid,
)
from backend.core.domain.value_objects.invitation_token import (
    generate_invitation_token,
    hash_invitation_token,
    verify_invitation_token,
)


class AcceptInvitationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, command: AcceptInvitationCommand) -> Invitation:
        token_hash = hash_invitation_token(command.token)
        invitation = self._unit_of_work.invitations.get_by_token_hash(token_hash)
        if invitation is None or not verify_invitation_token(
            command.token,
            invitation.token_hash,
        ):
            raise InvitationTokenInvalid()

        now = self._clock.now()
        if invitation.status is InvitationStatus.ACCEPTED:
            raise InvitationAlreadyAccepted(invitation.id)
        if invitation.status is InvitationStatus.REVOKED:
            raise InvitationAlreadyRevoked(invitation.id)
        if not invitation.is_acceptable(now=now):
            raise InvitationExpired(invitation.id)

        user = self._unit_of_work.users.get(command.accepting_user_id)
        if not user.can_authenticate():
            raise UserAlreadyDeactivated(user.id)
        if user.email != invitation.email:
            raise InvitationEmailMismatch()

        provision_membership_for_invitation(
            self._unit_of_work,
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role,
            now=now,
        )

        accepted_invitation = invitation.model_copy(
            update={
                "status": InvitationStatus.ACCEPTED,
                "accepted_at": now,
                "updated_at": now,
            }
        )
        self._unit_of_work.invitations.save(accepted_invitation)
        self._unit_of_work.commit()
        return accepted_invitation


class RevokeInvitationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, command: RevokeInvitationCommand) -> Invitation:
        invitation = self._unit_of_work.invitations.get(command.invitation_id)
        if invitation.status is InvitationStatus.ACCEPTED:
            raise InvitationAlreadyAccepted(invitation.id)
        if invitation.status is InvitationStatus.REVOKED:
            raise InvitationAlreadyRevoked(invitation.id)

        now = self._clock.now()
        revoked_invitation = invitation.model_copy(
            update={
                "status": InvitationStatus.REVOKED,
                "revoked_at": now,
                "updated_at": now,
            }
        )
        self._unit_of_work.invitations.save(revoked_invitation)
        self._unit_of_work.commit()
        return revoked_invitation


class ReissueInvitationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def handle(self, command: ReissueInvitationCommand) -> InvitationWithTokenResult:
        invitation = self._unit_of_work.invitations.get(command.invitation_id)
        if invitation.status is InvitationStatus.ACCEPTED:
            raise InvitationAlreadyAccepted(invitation.id)
        if invitation.status is InvitationStatus.REVOKED:
            raise InvitationAlreadyRevoked(invitation.id)

        now = self._clock.now()
        token, token_hash = generate_invitation_token()
        expires_at = default_invitation_expiration(
            now=now,
            ttl_days=DEFAULT_INVITATION_TTL_DAYS,
        )
        reissued_invitation = invitation.model_copy(
            update={
                "status": InvitationStatus.PENDING,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "updated_at": now,
                "accepted_at": None,
                "revoked_at": None,
            }
        )
        self._unit_of_work.invitations.save(reissued_invitation)
        self._unit_of_work.commit()
        return InvitationWithTokenResult(invitation=reissued_invitation, token=token)

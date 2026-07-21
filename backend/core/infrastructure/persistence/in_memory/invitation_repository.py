from __future__ import annotations

from backend.core.domain.entities.invitation import Invitation, InvitationStatus
from backend.core.domain.exceptions.invitation import InvitationNotFound
from backend.core.domain.repositories.invitation_repository import InvitationRepositoryContract
from backend.core.domain.value_objects import InvitationId, OrganizationId
from backend.core.domain.value_objects.invitation_list_criteria import (
    InvitationListCriteria,
    InvitationListResult,
)


class InMemoryInvitationRepository(InvitationRepositoryContract):
    def __init__(self) -> None:
        self._invitations_by_id: dict[InvitationId, Invitation] = {}
        self._invitations_by_token_hash: dict[str, InvitationId] = {}

    def add(self, invitation: Invitation) -> None:
        self._invitations_by_id[invitation.id] = invitation
        self._invitations_by_token_hash[invitation.token_hash] = invitation.id

    def get(self, invitation_id: InvitationId) -> Invitation:
        invitation = self._invitations_by_id.get(invitation_id)
        if invitation is None:
            raise InvitationNotFound(invitation_id)
        return invitation

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        invitation_id = self._invitations_by_token_hash.get(token_hash)
        if invitation_id is None:
            return None
        return self._invitations_by_id.get(invitation_id)

    def get_active_pending_by_organization_and_email(
        self,
        organization_id: OrganizationId,
        normalized_email: str,
    ) -> Invitation | None:
        for invitation in self._invitations_by_id.values():
            if invitation.organization_id != organization_id:
                continue
            if invitation.email != normalized_email:
                continue
            if invitation.status is not InvitationStatus.PENDING:
                continue
            return invitation
        return None

    def list_invitations(self, criteria: InvitationListCriteria) -> InvitationListResult:
        invitations = [
            invitation
            for invitation in self._invitations_by_id.values()
            if invitation.organization_id == criteria.organization_id
        ]

        if criteria.email is not None:
            normalized_email = criteria.email.strip().lower()
            invitations = [
                invitation
                for invitation in invitations
                if invitation.email == normalized_email
            ]
        if criteria.role is not None:
            invitations = [
                invitation
                for invitation in invitations
                if invitation.role.value == criteria.role.value
            ]
        if criteria.status is not None:
            invitations = [
                invitation
                for invitation in invitations
                if invitation.effective_status(now=criteria.as_of) is criteria.status
            ]

        invitations.sort(
            key=lambda invitation: invitation.created_at,
            reverse=not criteria.sort_ascending,
        )
        invitations.sort(key=lambda invitation: invitation.id.value)
        total = len(invitations)
        page = invitations[criteria.offset : criteria.offset + criteria.limit]

        return InvitationListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def save(self, invitation: Invitation) -> None:
        existing = self._invitations_by_id.get(invitation.id)
        if existing is None:
            raise InvitationNotFound(invitation.id)

        if existing.token_hash != invitation.token_hash:
            self._invitations_by_token_hash.pop(existing.token_hash, None)
            self._invitations_by_token_hash[invitation.token_hash] = invitation.id

        self._invitations_by_id[invitation.id] = invitation

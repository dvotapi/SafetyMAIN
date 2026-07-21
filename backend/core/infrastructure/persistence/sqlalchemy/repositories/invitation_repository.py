from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.domain.entities.invitation import Invitation, InvitationStatus
from backend.core.domain.exceptions.invitation import InvitationNotFound
from backend.core.domain.repositories.invitation_repository import InvitationRepositoryContract
from backend.core.domain.value_objects import InvitationId, OrganizationId
from backend.core.domain.value_objects.invitation_list_criteria import (
    InvitationListCriteria,
    InvitationListResult,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.invitation_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.invitation_model import (
    InvitationModel,
)


class SQLAlchemyInvitationRepository(InvitationRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, invitation: Invitation) -> None:
        self._session.add(to_model(invitation))

    def get(self, invitation_id: InvitationId) -> Invitation:
        model = self._session.get(InvitationModel, invitation_id.value)
        if model is None:
            raise InvitationNotFound(invitation_id)
        return to_domain(model)

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        statement = select(InvitationModel).where(InvitationModel.token_hash == token_hash)
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def get_active_pending_by_organization_and_email(
        self,
        organization_id: OrganizationId,
        normalized_email: str,
    ) -> Invitation | None:
        statement = select(InvitationModel).where(
            InvitationModel.organization_id == organization_id.value,
            InvitationModel.email == normalized_email,
            InvitationModel.status == InvitationStatus.PENDING.value,
        )
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def list_invitations(self, criteria: InvitationListCriteria) -> InvitationListResult:
        filters: list[object] = [
            InvitationModel.organization_id == criteria.organization_id.value
        ]
        if criteria.email is not None:
            filters.append(
                InvitationModel.email == criteria.email.strip().lower()
            )
        if criteria.role is not None:
            filters.append(InvitationModel.role == criteria.role.value)

        models = self._session.scalars(select(InvitationModel).where(*filters)).all()
        invitations = [to_domain(model) for model in models]

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
        model = self._session.get(InvitationModel, invitation.id.value)
        if model is None:
            raise InvitationNotFound(invitation.id)
        apply_to_model(model, invitation)

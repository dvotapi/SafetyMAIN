from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.invitation import Invitation
from backend.core.domain.value_objects import InvitationId, OrganizationId
from backend.core.domain.value_objects.invitation_list_criteria import (
    InvitationListCriteria,
    InvitationListResult,
)


class InvitationRepositoryContract(Protocol):
    def add(self, invitation: Invitation) -> None:
        ...

    def get(self, invitation_id: InvitationId) -> Invitation:
        ...

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        ...

    def get_active_pending_by_organization_and_email(
        self,
        organization_id: OrganizationId,
        normalized_email: str,
    ) -> Invitation | None:
        ...

    def list_invitations(self, criteria: InvitationListCriteria) -> InvitationListResult:
        ...

    def save(self, invitation: Invitation) -> None:
        ...

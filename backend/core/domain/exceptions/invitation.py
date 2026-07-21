from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import InvitationId, OrganizationId, UserId


class InvitationError(SafetyMainDomainError):
    """Base class for Invitation domain errors."""


class InvitationNotFound(InvitationError):
    def __init__(self, invitation_id: InvitationId) -> None:
        self.invitation_id = invitation_id
        super().__init__(f"Invitation was not found: {invitation_id.value}")


class InvitationTokenInvalid(InvitationError):
    def __init__(self) -> None:
        super().__init__("Invitation token is invalid.")


class DuplicateActiveInvitation(InvitationError):
    def __init__(self, *, organization_id: OrganizationId, email: str) -> None:
        self.organization_id = organization_id
        self.email = email
        super().__init__(
            "An active invitation already exists for this organization and email."
        )


class InvitationAlreadyAccepted(InvitationError):
    def __init__(self, invitation_id: InvitationId) -> None:
        self.invitation_id = invitation_id
        super().__init__("Invitation has already been accepted.")


class InvitationAlreadyRevoked(InvitationError):
    def __init__(self, invitation_id: InvitationId) -> None:
        self.invitation_id = invitation_id
        super().__init__("Invitation has already been revoked.")


class InvitationExpired(InvitationError):
    def __init__(self, invitation_id: InvitationId) -> None:
        self.invitation_id = invitation_id
        super().__init__("Invitation has expired.")


class InvitationEmailMismatch(InvitationError):
    def __init__(self) -> None:
        super().__init__("Authenticated user email does not match the invitation.")


class ExistingActiveMembership(InvitationError):
    def __init__(self, *, user_id: UserId, organization_id: OrganizationId) -> None:
        self.user_id = user_id
        self.organization_id = organization_id
        super().__init__(
            "User already has an active membership in the target organization."
        )

from __future__ import annotations

from backend.core.domain.value_objects import OrganizationId, UserId


class AuthorizationError(Exception):
    """Base class for application authorization errors."""


class OrganizationAccessDeniedError(AuthorizationError):
    def __init__(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        self.user_id = user_id
        self.organization_id = organization_id
        super().__init__(
            "Organization access was denied for user "
            f"{user_id.value} in organization {organization_id.value}"
        )


class MembershipRequiredError(AuthorizationError):
    def __init__(self, *, user_id: UserId | None = None) -> None:
        self.user_id = user_id
        super().__init__("Organization membership context is required.")


class OrganizationContextMismatchError(AuthorizationError):
    def __init__(self, *, user_id: UserId) -> None:
        self.user_id = user_id
        super().__init__("Organization context selection is invalid.")

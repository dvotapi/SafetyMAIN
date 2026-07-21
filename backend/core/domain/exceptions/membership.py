from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId


class MembershipError(SafetyMainDomainError):
    """Base class for Organization Membership domain errors."""


class MembershipNotFound(MembershipError):
    def __init__(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        self.user_id = user_id
        self.organization_id = organization_id
        super().__init__(
            "Organization membership was not found for user "
            f"{user_id.value} in organization {organization_id.value}"
        )


class InactiveMembership(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            f"Organization membership is not active: {membership_id.value}"
        )


class MembershipAlreadyActive(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            f"Organization membership is already active: {membership_id.value}"
        )


class MembershipAlreadyRevoked(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            f"Organization membership is already revoked: {membership_id.value}"
        )


class CannotActivateRevokedMembership(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            "Revoked organization membership cannot be reactivated: "
            f"{membership_id.value}"
        )


class MembershipByIdNotFound(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(f"Organization membership was not found: {membership_id.value}")


class DuplicateMembership(MembershipError):
    def __init__(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        self.user_id = user_id
        self.organization_id = organization_id
        super().__init__(
            "Organization membership already exists for user "
            f"{user_id.value} in organization {organization_id.value}"
        )


class InvalidMembershipRole(MembershipError):
    def __init__(self, role: str) -> None:
        self.role = role
        super().__init__(f"Membership role is invalid: {role}")


class SelfMembershipDeactivationError(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            "The current authorization membership cannot be deactivated."
        )


class SelfMembershipRoleDowngradeError(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            "The current authorization membership role cannot be downgraded."
        )


class LastOrganizationAdministratorError(MembershipError):
    def __init__(self, organization_id: OrganizationId) -> None:
        self.organization_id = organization_id
        super().__init__(
            "Organization must retain at least one active administrator."
        )


class MembershipAlreadyInactive(MembershipError):
    def __init__(self, membership_id: MembershipId) -> None:
        self.membership_id = membership_id
        super().__init__(
            f"Organization membership is already inactive: {membership_id.value}"
        )

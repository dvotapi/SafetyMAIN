from __future__ import annotations

from backend.core.application.exceptions.authorization import OrganizationAccessDeniedError
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.domain.value_objects import OrganizationId, UserId


class OrganizationAccessPolicy:
    """Requires an authenticated user with active organization membership."""

    def __init__(self, membership_verification: MembershipVerificationPort) -> None:
        self._membership_verification = membership_verification

    def authorize_organization_access(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        if not self._membership_verification.is_active_member(user_id, organization_id):
            raise OrganizationAccessDeniedError(
                user_id=user_id,
                organization_id=organization_id,
            )

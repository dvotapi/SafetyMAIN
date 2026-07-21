from __future__ import annotations

from backend.core.application.authorization.policies.organization_access_policy import (
    OrganizationAccessPolicy,
)
from backend.core.application.context.security_context import SecurityContext
from backend.core.application.exceptions.authorization import MembershipRequiredError
from backend.core.contracts.authorization_policy import AuthorizationPolicyPort
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.domain.value_objects import OrganizationId, UserId


class AuthorizationService:
    """Application authorization service independent of HTTP and JWT."""

    def __init__(
        self,
        organization_access_policy: AuthorizationPolicyPort | None = None,
        *,
        membership_verification: MembershipVerificationPort | None = None,
    ) -> None:
        if organization_access_policy is None:
            if membership_verification is None:
                raise ValueError(
                    "Either organization_access_policy or membership_verification "
                    "must be provided."
                )
            organization_access_policy = OrganizationAccessPolicy(
                membership_verification
            )

        self._organization_access_policy = organization_access_policy

    def require_organization_access(
        self,
        *,
        actor_user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        self._organization_access_policy.authorize_organization_access(
            user_id=actor_user_id,
            organization_id=organization_id,
        )

    def authorize_security_context(self, security_context: SecurityContext) -> None:
        if not security_context.is_authenticated or security_context.user_id is None:
            raise MembershipRequiredError()

        if security_context.organization_id is None:
            raise MembershipRequiredError(user_id=security_context.user_id)

        self.require_organization_access(
            actor_user_id=security_context.user_id,
            organization_id=security_context.organization_id,
        )

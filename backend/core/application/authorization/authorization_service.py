from __future__ import annotations

from backend.core.application.authorization.permission_evaluator import PermissionEvaluator
from backend.core.application.authorization.policies.organization_access_policy import (
    OrganizationAccessPolicy,
)
from backend.core.application.authorization.policies.permission_access_policy import (
    PermissionAccessPolicy,
)
from backend.core.application.context.security_context import SecurityContext
from backend.core.application.exceptions.authorization import MembershipRequiredError
from backend.core.contracts.authorization_policy import AuthorizationPolicyPort
from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.contracts.permission_policy import PermissionPolicyPort
from backend.core.domain.value_objects import OrganizationId, Permission, UserId


class AuthorizationService:
    """Application authorization service independent of HTTP and JWT."""

    def __init__(
        self,
        organization_access_policy: AuthorizationPolicyPort | None = None,
        *,
        membership_verification: MembershipVerificationPort | None = None,
        permission_policy: PermissionPolicyPort | None = None,
        membership_lookup: MembershipLookupPort | None = None,
        permission_evaluator: PermissionEvaluator | None = None,
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

        if permission_policy is not None:
            self._permission_policy = permission_policy
        elif permission_evaluator is not None:
            self._permission_policy = PermissionAccessPolicy(permission_evaluator)
        elif membership_lookup is not None:
            self._permission_policy = PermissionAccessPolicy(
                PermissionEvaluator(membership_lookup)
            )
        else:
            self._permission_policy = None

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

    def require_permission(
        self,
        *,
        actor_user_id: UserId,
        organization_id: OrganizationId,
        permission: Permission,
    ) -> None:
        if self._permission_policy is None:
            raise RuntimeError("Permission evaluation is not configured.")

        self.require_organization_access(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
        )
        self._permission_policy.authorize_permission(
            user_id=actor_user_id,
            organization_id=organization_id,
            permission=permission,
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

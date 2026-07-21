from __future__ import annotations

from backend.core.application.authorization.role_permission_resolver import (
    RolePermissionResolver,
)
from backend.core.application.exceptions.authorization import PermissionDeniedError
from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.domain.value_objects import OrganizationId, Permission, Role, UserId


class PermissionEvaluator:
    """Evaluates role-based permissions independent of HTTP and JWT."""

    def __init__(
        self,
        membership_lookup: MembershipLookupPort,
        role_permission_resolver: RolePermissionResolver | None = None,
    ) -> None:
        self._membership_lookup = membership_lookup
        self._role_permission_resolver = role_permission_resolver or RolePermissionResolver()

    def resolve_role(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Role | None:
        membership = self._membership_lookup.get_membership(user_id, organization_id)
        if membership is None or not membership.grants_organization_access():
            return None
        return membership.role

    def has_permission(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
        permission: Permission,
    ) -> bool:
        role = self.resolve_role(user_id=user_id, organization_id=organization_id)
        if role is None:
            return False

        granted_permissions = self._role_permission_resolver.resolve(role)
        return permission in granted_permissions

    def require_permission(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
        permission: Permission,
    ) -> None:
        role = self.resolve_role(user_id=user_id, organization_id=organization_id)
        if role is None:
            raise PermissionDeniedError(
                user_id=user_id,
                organization_id=organization_id,
                permission=permission,
            )

        granted_permissions = self._role_permission_resolver.resolve(role)
        if permission not in granted_permissions:
            raise PermissionDeniedError(
                user_id=user_id,
                organization_id=organization_id,
                permission=permission,
                role=role,
            )

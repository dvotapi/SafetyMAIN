from __future__ import annotations

from backend.core.application.authorization.permission_evaluator import PermissionEvaluator
from backend.core.domain.value_objects import OrganizationId, Permission, UserId


class PermissionAccessPolicy:
    """Requires an active member role that grants the requested permission."""

    def __init__(self, permission_evaluator: PermissionEvaluator) -> None:
        self._permission_evaluator = permission_evaluator

    def authorize_permission(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
        permission: Permission,
    ) -> None:
        self._permission_evaluator.require_permission(
            user_id=user_id,
            organization_id=organization_id,
            permission=permission,
        )

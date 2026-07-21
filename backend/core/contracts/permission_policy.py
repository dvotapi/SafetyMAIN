from __future__ import annotations

from typing import Protocol

from backend.core.domain.value_objects import OrganizationId, Permission, UserId


class PermissionPolicyPort(Protocol):
    """Application port for reusable permission policy evaluation."""

    def authorize_permission(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
        permission: Permission,
    ) -> None:
        ...

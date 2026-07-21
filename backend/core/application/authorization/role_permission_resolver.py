from __future__ import annotations

from backend.core.domain.value_objects.permission import Permission
from backend.core.domain.value_objects.role import Role
from backend.core.domain.value_objects.role_permissions import permissions_for_role


class RolePermissionResolver:
    """Resolves effective permissions for a membership role."""

    def resolve(self, role: Role) -> frozenset[Permission]:
        return permissions_for_role(role)

from __future__ import annotations

from backend.core.domain.value_objects.permission import Permission, SystemPermission
from backend.core.domain.value_objects.role import Role, SystemRole

SYSTEM_ROLE_PERMISSIONS: dict[SystemRole, frozenset[SystemPermission]] = {
    SystemRole.ADMIN: frozenset(SystemPermission),
    SystemRole.MEMBER: frozenset(
        {
            SystemPermission.KNOWLEDGE_OBJECT_READ,
            SystemPermission.KNOWLEDGE_OBJECT_WRITE,
            SystemPermission.RELATION_MANAGE,
        }
    ),
    SystemRole.AUDITOR: frozenset(
        {
            SystemPermission.KNOWLEDGE_OBJECT_READ,
        }
    ),
}


def permissions_for_role(role: Role) -> frozenset[Permission]:
    try:
        system_role = SystemRole(role.value)
    except ValueError as exc:
        raise ValueError(f"Unknown system role: {role.value}") from exc

    return frozenset(
        Permission.from_system_permission(permission)
        for permission in SYSTEM_ROLE_PERMISSIONS[system_role]
    )

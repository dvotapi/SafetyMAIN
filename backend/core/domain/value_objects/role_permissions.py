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
            SystemPermission.HAZARD_READ,
            SystemPermission.HAZARD_CREATE,
            SystemPermission.HAZARD_UPDATE,
            SystemPermission.RISK_READ,
            SystemPermission.RISK_CREATE,
            SystemPermission.RISK_UPDATE,
            SystemPermission.RISK_CONTROL_READ,
            SystemPermission.RISK_CONTROL_CREATE,
            SystemPermission.RISK_CONTROL_UPDATE,
            SystemPermission.RISK_CONTROL_ASSIGN,
            SystemPermission.RISK_CONTROL_IMPLEMENT,
            SystemPermission.RISK_CONTROL_REVIEW,
            SystemPermission.RISK_CONTROL_MATERIALIZE,
        }
    ),
    SystemRole.AUDITOR: frozenset(
        {
            SystemPermission.KNOWLEDGE_OBJECT_READ,
            SystemPermission.ORGANIZATION_READ,
            SystemPermission.MEMBERSHIP_READ,
            SystemPermission.USER_READ,
            SystemPermission.INVITATION_READ,
            SystemPermission.AUDIT_READ,
            SystemPermission.HAZARD_READ,
            SystemPermission.RISK_READ,
            SystemPermission.RISK_CONTROL_READ,
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

from __future__ import annotations

from backend.core.domain.value_objects.permission import Permission, SystemPermission

# Reusable permission policies mapped to the existing domain role-permission model.
# Relation read/write/delete operations require relation:manage because P3-002
# defines a single relation capability rather than granular relation permissions.
# Knowledge object delete requires knowledge_object:write for the same reason.

KNOWLEDGE_OBJECT_READ = Permission.from_system_permission(
    SystemPermission.KNOWLEDGE_OBJECT_READ
)
KNOWLEDGE_OBJECT_WRITE = Permission.from_system_permission(
    SystemPermission.KNOWLEDGE_OBJECT_WRITE
)
KNOWLEDGE_OBJECT_DELETE = Permission.from_system_permission(
    SystemPermission.KNOWLEDGE_OBJECT_WRITE
)
RELATION_READ = Permission.from_system_permission(SystemPermission.RELATION_MANAGE)
RELATION_WRITE = Permission.from_system_permission(SystemPermission.RELATION_MANAGE)
RELATION_DELETE = Permission.from_system_permission(SystemPermission.RELATION_MANAGE)
USER_READ = Permission.from_system_permission(SystemPermission.USER_READ)
USER_WRITE = Permission.from_system_permission(SystemPermission.USER_WRITE)
ORGANIZATION_READ = Permission.from_system_permission(SystemPermission.ORGANIZATION_READ)
ORGANIZATION_WRITE = Permission.from_system_permission(SystemPermission.ORGANIZATION_WRITE)
MEMBERSHIP_READ = Permission.from_system_permission(SystemPermission.MEMBERSHIP_READ)
MEMBERSHIP_WRITE = Permission.from_system_permission(SystemPermission.MEMBERSHIP_WRITE)
INVITATION_READ = Permission.from_system_permission(SystemPermission.INVITATION_READ)
INVITATION_WRITE = Permission.from_system_permission(SystemPermission.INVITATION_WRITE)
AUDIT_READ = Permission.from_system_permission(SystemPermission.AUDIT_READ)

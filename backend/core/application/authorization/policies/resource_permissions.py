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
HAZARD_READ = Permission.from_system_permission(SystemPermission.HAZARD_READ)
HAZARD_CREATE = Permission.from_system_permission(SystemPermission.HAZARD_CREATE)
HAZARD_UPDATE = Permission.from_system_permission(SystemPermission.HAZARD_UPDATE)
HAZARD_ACTIVATE = Permission.from_system_permission(SystemPermission.HAZARD_ACTIVATE)
HAZARD_ARCHIVE = Permission.from_system_permission(SystemPermission.HAZARD_ARCHIVE)
HAZARD_RESTORE = Permission.from_system_permission(SystemPermission.HAZARD_RESTORE)
RISK_READ = Permission.from_system_permission(SystemPermission.RISK_READ)
RISK_CREATE = Permission.from_system_permission(SystemPermission.RISK_CREATE)
RISK_UPDATE = Permission.from_system_permission(SystemPermission.RISK_UPDATE)
RISK_REVIEW = Permission.from_system_permission(SystemPermission.RISK_REVIEW)
RISK_APPROVE = Permission.from_system_permission(SystemPermission.RISK_APPROVE)
RISK_ARCHIVE = Permission.from_system_permission(SystemPermission.RISK_ARCHIVE)
RISK_CONTROL_READ = Permission.from_system_permission(SystemPermission.RISK_CONTROL_READ)
RISK_CONTROL_CREATE = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_CREATE
)
RISK_CONTROL_UPDATE = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_UPDATE
)
RISK_CONTROL_ASSIGN = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_ASSIGN
)
RISK_CONTROL_IMPLEMENT = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_IMPLEMENT
)
RISK_CONTROL_VERIFY = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_VERIFY
)
RISK_CONTROL_REVIEW = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_REVIEW
)
RISK_CONTROL_SUSPEND = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_SUSPEND
)
RISK_CONTROL_SUPERSEDE = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_SUPERSEDE
)
RISK_CONTROL_ARCHIVE = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_ARCHIVE
)
RISK_CONTROL_CANCEL = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_CANCEL
)
RISK_CONTROL_MATERIALIZE = Permission.from_system_permission(
    SystemPermission.RISK_CONTROL_MATERIALIZE
)

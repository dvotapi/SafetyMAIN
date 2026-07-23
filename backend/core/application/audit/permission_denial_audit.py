from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.core.domain.value_objects import OrganizationId, Permission, UserId
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.permission import SystemPermission

PERMISSION_DENIED_FAILURE_CODE = "permission_denied"

ADMINISTRATIVE_SYSTEM_PERMISSIONS: frozenset[SystemPermission] = frozenset(
    {
        SystemPermission.USER_READ,
        SystemPermission.USER_WRITE,
        SystemPermission.ORGANIZATION_READ,
        SystemPermission.ORGANIZATION_WRITE,
        SystemPermission.MEMBERSHIP_READ,
        SystemPermission.MEMBERSHIP_WRITE,
        SystemPermission.INVITATION_READ,
        SystemPermission.INVITATION_WRITE,
        SystemPermission.AUDIT_READ,
    }
)

_PERMISSION_TO_RESOURCE_TYPE: dict[str, AuditResourceType] = {
    SystemPermission.USER_READ.value: AuditResourceType.USER,
    SystemPermission.USER_WRITE.value: AuditResourceType.USER,
    SystemPermission.ORGANIZATION_READ.value: AuditResourceType.ORGANIZATION,
    SystemPermission.ORGANIZATION_WRITE.value: AuditResourceType.ORGANIZATION,
    SystemPermission.MEMBERSHIP_READ.value: AuditResourceType.MEMBERSHIP,
    SystemPermission.MEMBERSHIP_WRITE.value: AuditResourceType.MEMBERSHIP,
    SystemPermission.INVITATION_READ.value: AuditResourceType.INVITATION,
    SystemPermission.INVITATION_WRITE.value: AuditResourceType.INVITATION,
    SystemPermission.AUDIT_READ.value: AuditResourceType.AUDIT_EVENT,
}


def is_administrative_permission(permission: Permission) -> bool:
    try:
        system_permission = SystemPermission(permission.value)
    except ValueError:
        return False
    return system_permission in ADMINISTRATIVE_SYSTEM_PERMISSIONS


def resource_type_for_permission(permission: Permission) -> AuditResourceType:
    resource_type = _PERMISSION_TO_RESOURCE_TYPE.get(permission.value)
    if resource_type is None:
        raise ValueError(f"No audit resource type mapping for permission {permission.value}.")
    return resource_type


def permission_category(permission: Permission) -> str:
    return permission.value.split(":", maxsplit=1)[0]


@dataclass(frozen=True, slots=True)
class PermissionDenialAuditSpec:
    actor_user_id: UserId
    authorization_organization_id: OrganizationId
    required_permission: Permission
    resource_type: AuditResourceType
    http_method: str
    route_template: str
    resource_id: UUID | None = None
    target_organization_id: OrganizationId | None = None
    operation_id: str | None = None
    target_identifier_present: bool = False

    def metadata(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "required_permission": self.required_permission.value,
            "http_method": self.http_method,
            "route_template": self.route_template,
            "target_identifier_present": self.target_identifier_present,
            "permission_category": permission_category(self.required_permission),
        }
        if self.operation_id is not None:
            payload["operation_id"] = self.operation_id
        return payload

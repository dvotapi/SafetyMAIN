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
        SystemPermission.HAZARD_READ,
        SystemPermission.HAZARD_CREATE,
        SystemPermission.HAZARD_UPDATE,
        SystemPermission.HAZARD_ACTIVATE,
        SystemPermission.HAZARD_ARCHIVE,
        SystemPermission.HAZARD_RESTORE,
        SystemPermission.RISK_READ,
        SystemPermission.RISK_CREATE,
        SystemPermission.RISK_UPDATE,
        SystemPermission.RISK_REVIEW,
        SystemPermission.RISK_APPROVE,
        SystemPermission.RISK_ARCHIVE,
        SystemPermission.RISK_CONTROL_READ,
        SystemPermission.RISK_CONTROL_CREATE,
        SystemPermission.RISK_CONTROL_UPDATE,
        SystemPermission.RISK_CONTROL_ASSIGN,
        SystemPermission.RISK_CONTROL_IMPLEMENT,
        SystemPermission.RISK_CONTROL_VERIFY,
        SystemPermission.RISK_CONTROL_REVIEW,
        SystemPermission.RISK_CONTROL_SUSPEND,
        SystemPermission.RISK_CONTROL_SUPERSEDE,
        SystemPermission.RISK_CONTROL_ARCHIVE,
        SystemPermission.RISK_CONTROL_CANCEL,
        SystemPermission.RISK_CONTROL_MATERIALIZE,
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
    SystemPermission.HAZARD_READ.value: AuditResourceType.HAZARD,
    SystemPermission.HAZARD_CREATE.value: AuditResourceType.HAZARD,
    SystemPermission.HAZARD_UPDATE.value: AuditResourceType.HAZARD,
    SystemPermission.HAZARD_ACTIVATE.value: AuditResourceType.HAZARD,
    SystemPermission.HAZARD_ARCHIVE.value: AuditResourceType.HAZARD,
    SystemPermission.HAZARD_RESTORE.value: AuditResourceType.HAZARD,
    SystemPermission.RISK_READ.value: AuditResourceType.RISK,
    SystemPermission.RISK_CREATE.value: AuditResourceType.RISK,
    SystemPermission.RISK_UPDATE.value: AuditResourceType.RISK,
    SystemPermission.RISK_REVIEW.value: AuditResourceType.RISK,
    SystemPermission.RISK_APPROVE.value: AuditResourceType.RISK,
    SystemPermission.RISK_ARCHIVE.value: AuditResourceType.RISK,
    SystemPermission.RISK_CONTROL_READ.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_CREATE.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_UPDATE.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_ASSIGN.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_IMPLEMENT.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_VERIFY.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_REVIEW.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_SUSPEND.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_SUPERSEDE.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_ARCHIVE.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_CANCEL.value: AuditResourceType.RISK_CONTROL,
    SystemPermission.RISK_CONTROL_MATERIALIZE.value: AuditResourceType.RISK_CONTROL,
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

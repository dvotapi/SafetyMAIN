from __future__ import annotations

from backend.core.application.audit.permission_denial_audit import (
    PERMISSION_DENIED_FAILURE_CODE,
    is_administrative_permission,
    permission_category,
    resource_type_for_permission,
)
from backend.core.application.authorization.policies.resource_permissions import (
    AUDIT_READ,
    KNOWLEDGE_OBJECT_WRITE,
    MEMBERSHIP_WRITE,
    USER_READ,
)
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.permission import Permission


def test_administrative_permission_classification() -> None:
    assert is_administrative_permission(USER_READ) is True
    assert is_administrative_permission(MEMBERSHIP_WRITE) is True
    assert is_administrative_permission(AUDIT_READ) is True
    assert is_administrative_permission(KNOWLEDGE_OBJECT_WRITE) is False


def test_resource_type_mapping_for_admin_permissions() -> None:
    assert resource_type_for_permission(USER_READ) is AuditResourceType.USER
    assert resource_type_for_permission(AUDIT_READ) is AuditResourceType.AUDIT_EVENT
    assert resource_type_for_permission(MEMBERSHIP_WRITE) is AuditResourceType.MEMBERSHIP


def test_unknown_permission_is_not_administrative() -> None:
    custom = Permission(value="custom:permission")
    assert is_administrative_permission(custom) is False


def test_permission_category_extracts_prefix() -> None:
    assert permission_category(USER_READ) == "user"


def test_permission_denied_failure_code_is_stable() -> None:
    assert PERMISSION_DENIED_FAILURE_CODE == "permission_denied"

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.domain.value_objects import (
    MembershipId,
    Permission,
    Role,
    SystemPermission,
    SystemRole,
    UserId,
)
from backend.core.domain.value_objects.role_permissions import permissions_for_role


def test_user_id_wraps_uuid() -> None:
    value = uuid4()

    user_id = UserId(value=value)

    assert user_id.value == value


def test_user_id_rejects_invalid_uuid() -> None:
    with pytest.raises(ValidationError):
        UserId(value="not-a-uuid")


def test_membership_id_wraps_uuid() -> None:
    value = uuid4()

    membership_id = MembershipId(value=value)

    assert membership_id.value == value


def test_role_normalizes_value() -> None:
    role = Role(value=" Admin ")

    assert role.value == "admin"


def test_system_role_factory_methods() -> None:
    assert Role.admin().value == SystemRole.ADMIN.value
    assert Role.member().value == SystemRole.MEMBER.value
    assert Role.auditor().value == SystemRole.AUDITOR.value


def test_permission_from_system_permission() -> None:
    permission = Permission.from_system_permission(
        SystemPermission.KNOWLEDGE_OBJECT_READ
    )

    assert permission.value == "knowledge_object:read"


def test_permissions_for_member_role() -> None:
    permissions = permissions_for_role(Role.member())

    assert Permission.from_system_permission(
        SystemPermission.KNOWLEDGE_OBJECT_READ
    ) in permissions
    assert Permission.from_system_permission(
        SystemPermission.MEMBERSHIP_MANAGE
    ) not in permissions


def test_permissions_for_admin_role_includes_all_capabilities() -> None:
    permissions = permissions_for_role(Role.admin())

    assert len(permissions) == len(SystemPermission)

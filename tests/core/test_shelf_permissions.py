from __future__ import annotations

import pytest

from backend.core.application.audit.permission_denial_audit import (
    is_administrative_permission,
    resource_type_for_permission,
)
from backend.core.application.authorization.policies.resource_permissions import (
    SHELF_CURATE,
    SHELF_READ,
)
from backend.core.domain.value_objects import Role
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.role_permissions import permissions_for_role


@pytest.mark.parametrize(
    ("role", "can_read", "can_curate"),
    [
        (Role.admin(), True, True),
        (Role.member(), True, False),
        (Role.auditor(), True, False),
    ],
)
def test_shelf_permissions_by_role(role: Role, can_read: bool, can_curate: bool) -> None:
    granted = permissions_for_role(role)

    assert (SHELF_READ in granted) is can_read
    assert (SHELF_CURATE in granted) is can_curate


def test_shelf_permission_denials_are_audited_as_shelf_places() -> None:
    for permission in (SHELF_READ, SHELF_CURATE):
        assert is_administrative_permission(permission)
        assert resource_type_for_permission(permission) is AuditResourceType.SHELF_PLACE

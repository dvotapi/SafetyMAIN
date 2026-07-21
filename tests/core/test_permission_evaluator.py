from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.authorization.permission_evaluator import PermissionEvaluator
from backend.core.application.authorization.policies.resource_permissions import (
    KNOWLEDGE_OBJECT_WRITE,
)
from backend.core.application.authorization.role_permission_resolver import (
    RolePermissionResolver,
)
from backend.core.application.exceptions.authorization import PermissionDeniedError
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.domain.value_objects.permission import Permission, SystemPermission
from backend.core.infrastructure.auth.in_memory_membership_store import (
    InMemoryMembershipStore,
)


def test_role_permission_resolver_returns_permissions_for_member_role() -> None:
    resolver = RolePermissionResolver()

    permissions = resolver.resolve(Role.member())

    assert Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_READ) in permissions
    assert Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_WRITE) in permissions
    assert Permission.from_system_permission(SystemPermission.RELATION_MANAGE) in permissions


def test_role_permission_resolver_returns_read_only_permissions_for_auditor_role() -> None:
    resolver = RolePermissionResolver()

    permissions = resolver.resolve(Role.auditor())

    assert Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_READ) in permissions
    assert Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_WRITE) not in permissions
    assert Permission.from_system_permission(SystemPermission.RELATION_MANAGE) not in permissions


def test_permission_evaluator_allows_member_write_permission() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.member(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    evaluator = PermissionEvaluator(membership_store)

    assert evaluator.has_permission(
        user_id=user_id,
        organization_id=organization_id,
        permission=KNOWLEDGE_OBJECT_WRITE,
    )


def test_permission_evaluator_denies_auditor_write_permission() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.auditor(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    evaluator = PermissionEvaluator(membership_store)

    with pytest.raises(PermissionDeniedError) as exc_info:
        evaluator.require_permission(
            user_id=user_id,
            organization_id=organization_id,
            permission=KNOWLEDGE_OBJECT_WRITE,
        )

    assert exc_info.value.user_id == user_id
    assert exc_info.value.organization_id == organization_id
    assert exc_info.value.permission == KNOWLEDGE_OBJECT_WRITE
    assert exc_info.value.role == Role.auditor()


def test_permission_evaluator_denies_unknown_role() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role(value="custom-role"),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    evaluator = PermissionEvaluator(membership_store)

    with pytest.raises(PermissionDeniedError):
        evaluator.require_permission(
            user_id=user_id,
            organization_id=organization_id,
            permission=KNOWLEDGE_OBJECT_WRITE,
        )


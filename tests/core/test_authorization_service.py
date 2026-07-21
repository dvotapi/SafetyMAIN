from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.authorization.authorization_service import AuthorizationService
from backend.core.application.authorization.policies.organization_access_policy import (
    OrganizationAccessPolicy,
)
from backend.core.application.context.security_context import SecurityContext
from backend.core.application.exceptions.authorization import (
    MembershipRequiredError,
    OrganizationAccessDeniedError,
    PermissionDeniedError,
)
from backend.core.domain.value_objects.permission import Permission, SystemPermission
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_membership_store import (
    InMemoryMembershipStore,
)


def test_authorization_service_allows_active_member() -> None:
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
    service = AuthorizationService(membership_verification=membership_store)

    service.require_organization_access(
        actor_user_id=user_id,
        organization_id=organization_id,
    )


def test_authorization_service_denies_non_member() -> None:
    service = AuthorizationService(membership_verification=InMemoryMembershipStore())
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())

    with pytest.raises(OrganizationAccessDeniedError) as exc_info:
        service.require_organization_access(
            actor_user_id=user_id,
            organization_id=organization_id,
        )

    assert exc_info.value.user_id == user_id
    assert exc_info.value.organization_id == organization_id


def test_authorization_service_requires_organization_in_security_context() -> None:
    service = AuthorizationService(membership_verification=InMemoryMembershipStore())
    context = SecurityContext.authenticated(user_id=UserId(value=uuid4()))

    with pytest.raises(MembershipRequiredError):
        service.authorize_security_context(context)


def test_organization_access_policy_uses_membership_verification_port() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())

    class FakeMembershipVerification:
        def is_active_member(
            self,
            candidate_user_id: UserId,
            candidate_organization_id: OrganizationId,
        ) -> bool:
            return (
                candidate_user_id == user_id
                and candidate_organization_id == organization_id
            )

    policy = OrganizationAccessPolicy(FakeMembershipVerification())
    service = AuthorizationService(organization_access_policy=policy)

    service.require_organization_access(
        actor_user_id=user_id,
        organization_id=organization_id,
    )


def test_authorization_service_allows_member_permission() -> None:
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
    service = AuthorizationService(
        membership_verification=membership_store,
        membership_lookup=membership_store,
    )

    service.require_permission(
        actor_user_id=user_id,
        organization_id=organization_id,
        permission=Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_WRITE),
    )


def test_authorization_service_denies_auditor_write_permission() -> None:
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
    service = AuthorizationService(
        membership_verification=membership_store,
        membership_lookup=membership_store,
    )

    with pytest.raises(PermissionDeniedError) as exc_info:
        service.require_permission(
            actor_user_id=user_id,
            organization_id=organization_id,
            permission=Permission.from_system_permission(
                SystemPermission.KNOWLEDGE_OBJECT_WRITE
            ),
        )

    assert exc_info.value.role == Role.auditor()

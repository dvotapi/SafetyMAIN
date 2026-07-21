from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.application.exceptions.authorization import (
    MembershipRequiredError,
    OrganizationContextMismatchError,
)
from backend.core.application.tenant.tenant_context_resolver import TenantContextResolver
from backend.core.domain.value_objects import OrganizationId, UserId


def test_tenant_context_resolver_uses_token_organization_when_present() -> None:
    user_id = UserId(value=uuid4())
    token_organization_id = OrganizationId(value=uuid4())
    resolver = TenantContextResolver(_FakeMembershipLookup())

    resolved = resolver.resolve_organization_id(
        user_id=user_id,
        token_organization_id=token_organization_id,
        header_organization_id=None,
    )

    assert resolved == token_organization_id


def test_tenant_context_resolver_falls_back_to_header() -> None:
    user_id = UserId(value=uuid4())
    header_organization_id = OrganizationId(value=uuid4())
    resolver = TenantContextResolver(_FakeMembershipLookup())

    resolved = resolver.resolve_organization_id(
        user_id=user_id,
        token_organization_id=None,
        header_organization_id=header_organization_id,
    )

    assert resolved == header_organization_id


def test_tenant_context_resolver_rejects_conflicting_organization_selection() -> None:
    user_id = UserId(value=uuid4())
    resolver = TenantContextResolver(_FakeMembershipLookup())

    with pytest.raises(OrganizationContextMismatchError):
        resolver.resolve_organization_id(
            user_id=user_id,
            token_organization_id=OrganizationId(value=uuid4()),
            header_organization_id=OrganizationId(value=uuid4()),
        )


def test_tenant_context_resolver_uses_default_organization() -> None:
    user_id = UserId(value=uuid4())
    default_organization_id = OrganizationId(value=uuid4())
    resolver = TenantContextResolver(
        _FakeMembershipLookup(),
        default_organization_id=default_organization_id,
    )

    resolved = resolver.resolve_organization_id(
        user_id=user_id,
        token_organization_id=None,
        header_organization_id=None,
    )

    assert resolved == default_organization_id


def test_tenant_context_resolver_requires_context_when_unresolved() -> None:
    user_id = UserId(value=uuid4())
    resolver = TenantContextResolver(_FakeMembershipLookup())

    with pytest.raises(MembershipRequiredError):
        resolver.resolve_organization_id(
            user_id=user_id,
            token_organization_id=None,
            header_organization_id=None,
        )


class _FakeMembershipLookup:
    def get_membership(self, user_id: UserId, organization_id: OrganizationId):
        return None

    def list_memberships_for_user(self, user_id: UserId):
        return ()

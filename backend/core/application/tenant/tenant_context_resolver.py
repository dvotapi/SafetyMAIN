from __future__ import annotations

from backend.core.application.context.security_context import SecurityContext
from backend.core.application.context.tenant_context import TenantContext
from backend.core.application.exceptions.authorization import (
    MembershipRequiredError,
    OrganizationContextMismatchError,
)
from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.domain.value_objects import OrganizationId, UserId


class TenantContextResolver:
    """Resolves organization tenant context for authenticated requests."""

    def __init__(
        self,
        membership_lookup: MembershipLookupPort,
        *,
        default_organization_id: OrganizationId | None = None,
    ) -> None:
        self._membership_lookup = membership_lookup
        self._default_organization_id = default_organization_id

    def resolve_organization_id(
        self,
        *,
        user_id: UserId,
        token_organization_id: OrganizationId | None,
        header_organization_id: OrganizationId | None,
    ) -> OrganizationId:
        if (
            token_organization_id is not None
            and header_organization_id is not None
            and token_organization_id != header_organization_id
        ):
            raise OrganizationContextMismatchError(user_id=user_id)

        if token_organization_id is not None:
            return token_organization_id

        if header_organization_id is not None:
            return header_organization_id

        if self._default_organization_id is not None:
            return self._default_organization_id

        active_memberships = tuple(
            membership
            for membership in self._membership_lookup.list_memberships_for_user(user_id)
            if membership.grants_organization_access()
        )
        if len(active_memberships) == 1:
            return active_memberships[0].organization_id

        raise MembershipRequiredError(user_id=user_id)

    def build_tenant_context(
        self,
        *,
        security_context: SecurityContext,
        organization_id: OrganizationId,
    ) -> TenantContext:
        return TenantContext(
            security_context=security_context.with_organization(organization_id),
            organization_id=organization_id,
        )

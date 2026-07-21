from __future__ import annotations

from typing import Protocol

from backend.core.domain.value_objects import OrganizationId, UserId


class AuthorizationPolicyPort(Protocol):
    """Application port for reusable authorization policy evaluation."""

    def authorize_organization_access(
        self,
        *,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> None:
        ...

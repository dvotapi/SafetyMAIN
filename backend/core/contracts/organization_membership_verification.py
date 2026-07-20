from __future__ import annotations

from typing import Protocol

from backend.core.domain.value_objects import OrganizationId, UserId


class OrganizationMembershipVerificationPort(Protocol):
    """Application port for verifying tenant access through membership."""

    def is_active_member(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> bool:
        ...

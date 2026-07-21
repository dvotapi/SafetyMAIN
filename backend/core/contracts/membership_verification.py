from __future__ import annotations

from typing import Protocol

from backend.core.domain.value_objects import OrganizationId, UserId


class MembershipVerificationPort(Protocol):
    """Application port for verifying active organization membership."""

    def is_active_member(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> bool:
        ...

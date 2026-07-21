from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.context.security_context import SecurityContext
from backend.core.domain.value_objects import OrganizationId, UserId


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Resolved tenant boundary for a business request."""

    security_context: SecurityContext
    organization_id: OrganizationId

    @property
    def actor_user_id(self) -> UserId | None:
        return self.security_context.actor_user_id

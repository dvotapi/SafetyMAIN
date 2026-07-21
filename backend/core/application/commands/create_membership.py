from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import OrganizationId, Role, UserId


@dataclass(frozen=True, slots=True)
class CreateMembershipCommand:
    user_id: UserId
    organization_id: OrganizationId
    role: Role
    is_active: bool = True
    audit_context: AuditContext | None = None

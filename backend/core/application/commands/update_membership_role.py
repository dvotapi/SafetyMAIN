from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.application.policies.membership_administration import (
    MembershipAuthorizationContext,
)
from backend.core.domain.value_objects import MembershipId, Role


@dataclass(frozen=True, slots=True)
class UpdateMembershipRoleCommand:
    membership_id: MembershipId
    role: Role
    authorization: MembershipAuthorizationContext
    audit_context: AuditContext | None = None

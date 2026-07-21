from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.core.application.audit.administrative_audit_recorder import AuditContext
from backend.core.domain.value_objects import InvitationId, OrganizationId, Role, UserId


@dataclass(frozen=True, slots=True)
class CreateInvitationCommand:
    organization_id: OrganizationId
    email: str
    role: Role
    created_by: UserId
    expires_at: datetime | None = None
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class RevokeInvitationCommand:
    invitation_id: InvitationId
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class ReissueInvitationCommand:
    invitation_id: InvitationId
    audit_context: AuditContext | None = None


@dataclass(frozen=True, slots=True)
class AcceptInvitationCommand:
    token: str
    accepting_user_id: UserId
    audit_context: AuditContext | None = None

from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.administrative_audit_recorder import AuditContext


@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    email: str
    display_name: str
    is_active: bool = True
    audit_context: AuditContext | None = None

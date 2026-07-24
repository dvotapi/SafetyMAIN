from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
)


@dataclass(frozen=True, slots=True)
class AuthenticateUserCommand:
    email: str
    password: str
    audit_context: AuthenticationAuditContext | None = None

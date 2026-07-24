from __future__ import annotations

from dataclasses import dataclass

from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
)


@dataclass(frozen=True, slots=True)
class RefreshAuthenticationCommand:
    refresh_token: str
    audit_context: AuthenticationAuditContext | None = None

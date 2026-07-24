from __future__ import annotations

from fastapi import Request

from backend.api.middleware import get_request_id
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
)


def build_authentication_audit_context(request: Request) -> AuthenticationAuditContext:
    """Extract safe authentication audit metadata at the API boundary.

    Uses the direct ASGI client address only. Forwarded IP headers are ignored
    unless an explicit trusted-proxy policy exists.
    """

    client = request.client
    client_ip = client.host if client is not None else None
    user_agent = request.headers.get("user-agent")

    return AuthenticationAuditContext(
        request_id=get_request_id(request),
        actor_user_id=None,
        organization_id=None,
        client_ip=client_ip,
        user_agent=user_agent,
    )

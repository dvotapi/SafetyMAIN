from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.application.commands.user_lifecycle import DeactivateUserCommand
from backend.core.application.handlers.create_user import CreateUserHandler
from backend.core.application.handlers.user_lifecycle import DeactivateUserHandler
from backend.core.application.services.refresh_session_factory import (
    create_refresh_token_session,
)
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionRevocationReason,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryRefreshTokenSessionRepository,
    InMemoryUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock
from tests.core.audit_test_support import make_admin_audit_stack


def test_deactivate_user_revokes_active_refresh_sessions() -> None:
    refresh_sessions = InMemoryRefreshTokenSessionRepository()
    stack = make_admin_audit_stack(refresh_sessions=refresh_sessions)
    user = CreateUserHandler(stack.uow, stack.audit).handle(
        CreateUserCommand(
            email="session-owner@example.com",
            display_name="Session Owner",
            audit_context=stack.ctx,
        )
    )
    now = datetime.now(UTC)
    first, _ = create_refresh_token_session(
        user_id=user.id,
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    second, _ = create_refresh_token_session(
        user_id=user.id,
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    other, _ = create_refresh_token_session(
        user_id=UserId(value=uuid4()),
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    refresh_sessions.add(first)
    refresh_sessions.add(second)
    refresh_sessions.add(other)

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            audit_events=stack.audit_events,
            refresh_sessions=refresh_sessions,
        )

    recorder = AuthenticationSecurityEventRecorder(UtcClock(), uow_factory)
    DeactivateUserHandler(stack.uow, stack.audit, recorder).handle(
        DeactivateUserCommand(user_id=user.id, audit_context=stack.ctx)
    )

    assert refresh_sessions.get_by_id(first.session_id).is_revoked()
    assert refresh_sessions.get_by_id(second.session_id).is_revoked()
    assert (
        refresh_sessions.get_by_id(first.session_id).revocation_reason
        is RefreshSessionRevocationReason.USER_DEACTIVATED
    )
    assert not refresh_sessions.get_by_id(other.session_id).is_revoked()

    revoked_events = [
        event
        for event in stack.audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_SESSION_REVOKED
    ]
    assert len(revoked_events) == 1
    assert revoked_events[0].metadata["revoked_session_count"] == 2

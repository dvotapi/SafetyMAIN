from __future__ import annotations

from collections.abc import Callable

from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.logout import LogoutCommand
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.token_service import (
    TokenServiceContract,
    TokenValidationError,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionRevocationReason,
    RefreshTokenIdHash,
)

UowFactory = Callable[[], UnitOfWorkContract]


class LogoutHandler:
    """Revokes the refresh session for a presented refresh token.

    Invalid tokens and already-rotated tokens are treated as already-logged-out
    successes so the endpoint cannot be used as a session-existence oracle.
    Only the current refresh jti may revoke an active session.
    """

    def __init__(
        self,
        token_service: TokenServiceContract,
        security_event_recorder: AuthenticationSecurityEventRecorder,
        uow_factory: UowFactory,
        clock: ClockContract,
    ) -> None:
        self._token_service = token_service
        self._security_event_recorder = security_event_recorder
        self._uow_factory = uow_factory
        self._clock = clock

    def handle(self, command: LogoutCommand) -> None:
        audit_context = command.audit_context or AuthenticationAuditContext()
        try:
            claims = self._token_service.decode_refresh_token(command.refresh_token)
        except TokenValidationError:
            self._security_event_recorder.record_logout_succeeded(audit_context)
            return

        presented_hash = RefreshTokenIdHash(value=hash_refresh_token_jti(claims.jti))
        now = self._clock.now()
        revoked = False
        with self._uow_factory() as unit_of_work:
            session = unit_of_work.refresh_sessions.get_by_id(claims.session_id)
            if (
                session is not None
                and not session.is_revoked()
                and session.current_token_id_hash == presented_hash
            ):
                unit_of_work.refresh_sessions.revoke(
                    claims.session_id,
                    revoked_at=now,
                    reason=RefreshSessionRevocationReason.LOGOUT,
                )
                unit_of_work.commit()
                revoked = True

        self._security_event_recorder.record_logout_succeeded(
            audit_context,
            user_id=claims.user_id if revoked else None,
            session_id=claims.session_id if revoked else None,
            revocation_reason=(
                RefreshSessionRevocationReason.LOGOUT.value if revoked else None
            ),
        )

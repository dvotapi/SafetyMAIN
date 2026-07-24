from __future__ import annotations

from collections.abc import Callable

from backend.core.application.audit.authentication_failure_codes import (
    refresh_failure_code_for_exception,
    refresh_failure_code_for_token_error,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import InvalidRefreshTokenError
from backend.core.application.services.refresh_session_rotation import (
    revoke_session_for_reuse,
    rotate_refresh_session,
    validate_refresh_session_against_claims,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.token_service import (
    AuthenticationTokens,
    TokenServiceContract,
    TokenValidationError,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.exceptions.refresh_session import (
    RefreshSessionError,
    RefreshTokenReuseDetected,
)
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import RefreshSessionId

UowFactory = Callable[[], UnitOfWorkContract]


class RefreshAuthenticationHandler:
    def __init__(
        self,
        token_service: TokenServiceContract,
        security_event_recorder: AuthenticationSecurityEventRecorder,
        uow_factory: UowFactory,
        clock: ClockContract,
        *,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._token_service = token_service
        self._security_event_recorder = security_event_recorder
        self._uow_factory = uow_factory
        self._clock = clock
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    def handle(self, command: RefreshAuthenticationCommand) -> AuthenticationTokens:
        audit_context = command.audit_context or AuthenticationAuditContext()
        try:
            claims = self._token_service.decode_refresh_token(command.refresh_token)
            now = self._clock.now()
            reuse_user_id: UserId | None = None
            reuse_session_id: RefreshSessionId | None = None
            tokens: AuthenticationTokens | None = None

            with self._uow_factory() as unit_of_work:
                session = unit_of_work.refresh_sessions.get_for_update(claims.session_id)
                try:
                    validated = validate_refresh_session_against_claims(
                        session,
                        claims,
                        now=now,
                    )
                except RefreshTokenReuseDetected:
                    if session is not None:
                        revoke_session_for_reuse(
                            unit_of_work,
                            session_id=session.session_id,
                            now=now,
                        )
                        unit_of_work.commit()
                        reuse_user_id = session.user_id
                        reuse_session_id = session.session_id
                    else:
                        raise
                else:
                    tokens = rotate_refresh_session(
                        unit_of_work,
                        self._token_service,
                        session=validated,
                        claims=claims,
                        now=now,
                        sliding_ttl_seconds=self._refresh_token_ttl_seconds,
                    )
                    unit_of_work.commit()

            if reuse_session_id is not None and reuse_user_id is not None:
                self._security_event_recorder.record_refresh_reuse_detected(
                    audit_context,
                    user_id=reuse_user_id,
                    session_id=reuse_session_id,
                )
                raise InvalidRefreshTokenError()

            assert tokens is not None
            self._security_event_recorder.record_refresh_succeeded(
                audit_context,
                user_id=claims.user_id,
                session_id=claims.session_id,
            )
            return tokens
        except InvalidRefreshTokenError:
            raise
        except TokenValidationError as exc:
            self._security_event_recorder.record_refresh_failed(
                audit_context,
                failure_reason=refresh_failure_code_for_token_error(exc),
            )
            raise InvalidRefreshTokenError() from exc
        except RefreshSessionError as exc:
            self._security_event_recorder.record_refresh_failed(
                audit_context,
                failure_reason=refresh_failure_code_for_exception(exc),
            )
            raise InvalidRefreshTokenError() from exc

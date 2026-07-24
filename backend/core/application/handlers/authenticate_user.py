from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from backend.core.application.audit.authentication_failure_codes import (
    LOGIN_FAILURE_CODES_BY_EXCEPTION,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
)
from backend.core.application.services.refresh_session_factory import (
    create_refresh_token_session,
    remaining_refresh_ttl_seconds,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.password_hasher import PasswordHasherContract
from backend.core.contracts.token_service import (
    AuthenticationTokens,
    RefreshTokenIssueSpec,
    TokenServiceContract,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.contracts.user_credentials import UserCredentialsPort
from backend.core.contracts.user_lookup import UserLookupPort
from backend.core.domain.value_objects import UserId

UowFactory = Callable[[], UnitOfWorkContract]


class AuthenticateUserHandler:
    def __init__(
        self,
        user_lookup: UserLookupPort,
        user_credentials: UserCredentialsPort,
        password_hasher: PasswordHasherContract,
        token_service: TokenServiceContract,
        security_event_recorder: AuthenticationSecurityEventRecorder,
        uow_factory: UowFactory,
        clock: ClockContract,
        *,
        refresh_token_ttl_seconds: int,
        refresh_absolute_ttl_seconds: int,
    ) -> None:
        self._user_lookup = user_lookup
        self._user_credentials = user_credentials
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._security_event_recorder = security_event_recorder
        self._uow_factory = uow_factory
        self._clock = clock
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._refresh_absolute_ttl_seconds = refresh_absolute_ttl_seconds

    def handle(self, command: AuthenticateUserCommand) -> AuthenticationTokens:
        audit_context = command.audit_context or AuthenticationAuditContext()
        normalized_email = command.email.strip().lower()
        resolved_user_id: UserId | None = None

        try:
            user = self._user_lookup.get_user_by_email(normalized_email)
            if user is None:
                raise InvalidCredentialsError()

            resolved_user_id = user.id

            if not user.can_authenticate():
                raise AuthenticationForbiddenError()

            password_hash = self._user_credentials.get_password_hash(user.id)
            if password_hash is None or not self._password_hasher.verify_password(
                command.password,
                password_hash,
            ):
                raise InvalidCredentialsError()

            now = self._clock.now()
            session, raw_jti = create_refresh_token_session(
                user_id=user.id,
                now=now,
                sliding_ttl_seconds=self._refresh_token_ttl_seconds,
                absolute_ttl_seconds=self._refresh_absolute_ttl_seconds,
                jti=str(uuid4()),
            )
            ttl_seconds = remaining_refresh_ttl_seconds(
                now=now,
                expires_at=session.expires_at,
            )
            tokens = self._token_service.issue_tokens(
                user.id,
                refresh=RefreshTokenIssueSpec(
                    session_id=session.session_id,
                    family_id=session.family_id,
                    jti=raw_jti,
                    ttl_seconds=ttl_seconds,
                ),
            )
            with self._uow_factory() as unit_of_work:
                unit_of_work.refresh_sessions.add(session)
                unit_of_work.commit()

            self._security_event_recorder.record_login_succeeded(
                audit_context,
                user_id=user.id,
            )
            return tokens
        except (InvalidCredentialsError, AuthenticationForbiddenError) as error:
            failure_reason = LOGIN_FAILURE_CODES_BY_EXCEPTION[type(error)]
            self._security_event_recorder.record_login_failed(
                audit_context,
                failure_reason=failure_reason,
                user_id=resolved_user_id,
            )
            raise

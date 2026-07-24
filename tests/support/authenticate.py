from __future__ import annotations

from collections.abc import Callable

from backend.bootstrap.container import AppContainer
from backend.bootstrap.settings import AppSettings
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.infrastructure.time.utc_clock import UtcClock
from tests.core.audit_test_support import make_authentication_security_event_recorder


def build_authenticate_user_handler(
    container: AppContainer,
    settings: AppSettings,
    *,
    security_event_recorder: AuthenticationSecurityEventRecorder | None = None,
    uow_factory: Callable[[], UnitOfWorkContract] | None = None,
) -> AuthenticateUserHandler:
    recorder = security_event_recorder or make_authentication_security_event_recorder()[0]
    factory = uow_factory or container.uow_factory
    return AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
        security_event_recorder=recorder,
        uow_factory=factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        refresh_absolute_ttl_seconds=settings.jwt_refresh_absolute_ttl_seconds,
    )

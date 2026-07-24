from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import InvalidRefreshTokenError
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import RefreshTokenIdHash
from backend.core.infrastructure.auth.sqlalchemy_identity_adapter import (
    SQLAlchemyIdentityAdapter,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def _settings(database_url: str) -> AppSettings:
    return AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=database_url,
        cors_allowed_origins=(),
        jwt_secret_key="refresh-session-secret-key-32chars!",
        jwt_issuer="safetymain-test",
        auth_enforcement=True,
        jwt_access_token_ttl_seconds=900,
        jwt_refresh_token_ttl_seconds=3600,
        jwt_refresh_absolute_ttl_seconds=7200,
        refresh_token_rotation_enabled=True,
    )


@pytest.mark.db
def test_refresh_session_concurrent_rotation(
    database_url: str,
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    settings = _settings(database_url)
    container = create_container(settings)
    assert container.session_factory is not None
    now = datetime.now(UTC)
    user = User(
        id=UserId(value=uuid4()),
        email=f"refresh-concurrent-{uuid4()}@example.com",
        display_name="Refresh Concurrent",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    password = "concurrent-password"
    password_hash = container.password_hasher.hash_password(password)
    assert isinstance(container.identity_store, SQLAlchemyIdentityAdapter)
    container.identity_store.register_user(user, password_hash)

    recorder = AuthenticationSecurityEventRecorder(UtcClock(), container.uow_factory)
    authenticate = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
        security_event_recorder=recorder,
        uow_factory=container.uow_factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        refresh_absolute_ttl_seconds=settings.jwt_refresh_absolute_ttl_seconds,
    )
    tokens = authenticate.handle(
        AuthenticateUserCommand(email=user.email, password=password)
    )
    barrier = Barrier(2)
    outcomes: list[str] = []

    def refresh_once() -> None:
        handler = RefreshAuthenticationHandler(
            token_service=container.token_service,
            security_event_recorder=recorder,
            uow_factory=container.uow_factory,
            clock=UtcClock(),
            refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        )
        try:
            barrier.wait(timeout=30)
            handler.handle(
                RefreshAuthenticationCommand(refresh_token=tokens.refresh_token)
            )
            outcomes.append("ok")
        except InvalidRefreshTokenError:
            outcomes.append("rejected")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(refresh_once) for _ in range(2)]
        for future in futures:
            future.result(timeout=60)

    assert sorted(outcomes) == ["ok", "rejected"]

    claims = container.token_service.decode_refresh_token(tokens.refresh_token)
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        session = uow.refresh_sessions.get_by_id(claims.session_id)
        assert session is not None
        assert session.current_token_id_hash != RefreshTokenIdHash(
            value=hash_refresh_token_jti(claims.jti)
        )

    with pytest.raises(InvalidRefreshTokenError):
        RefreshAuthenticationHandler(
            token_service=container.token_service,
            security_event_recorder=recorder,
            uow_factory=container.uow_factory,
            clock=UtcClock(),
            refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        ).handle(RefreshAuthenticationCommand(refresh_token=tokens.refresh_token))

    container.dispose()


@pytest.mark.db
def test_refresh_session_survives_container_restart(
    database_url: str,
    migrated_engine,
) -> None:
    settings = _settings(database_url)
    first = create_container(settings)
    now = datetime.now(UTC)
    user = User(
        id=UserId(value=uuid4()),
        email=f"refresh-restart-{uuid4()}@example.com",
        display_name="Refresh Restart",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    password = "restart-password"
    password_hash = first.password_hasher.hash_password(password)
    assert first.session_factory is not None
    assert isinstance(first.identity_store, SQLAlchemyIdentityAdapter)
    first.identity_store.register_user(user, password_hash)

    recorder = AuthenticationSecurityEventRecorder(UtcClock(), first.uow_factory)
    tokens = AuthenticateUserHandler(
        user_lookup=first.user_lookup,
        user_credentials=first.user_credentials,
        password_hasher=first.password_hasher,
        token_service=first.token_service,
        security_event_recorder=recorder,
        uow_factory=first.uow_factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        refresh_absolute_ttl_seconds=settings.jwt_refresh_absolute_ttl_seconds,
    ).handle(AuthenticateUserCommand(email=user.email, password=password))
    original_refresh = tokens.refresh_token
    first.dispose()

    second = create_container(settings)
    try:
        recorder = AuthenticationSecurityEventRecorder(UtcClock(), second.uow_factory)
        refresh_handler = RefreshAuthenticationHandler(
            token_service=second.token_service,
            security_event_recorder=recorder,
            uow_factory=second.uow_factory,
            clock=UtcClock(),
            refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        )
        rotated = refresh_handler.handle(
            RefreshAuthenticationCommand(refresh_token=original_refresh)
        )
        assert rotated.refresh_token != original_refresh
        again = refresh_handler.handle(
            RefreshAuthenticationCommand(refresh_token=rotated.refresh_token)
        )
        assert again.refresh_token != rotated.refresh_token
        with pytest.raises(InvalidRefreshTokenError):
            refresh_handler.handle(
                RefreshAuthenticationCommand(refresh_token=original_refresh)
            )
    finally:
        second.dispose()

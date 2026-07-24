from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.auth.in_memory_identity_store import (
    InMemoryIdentityStore,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryRefreshTokenSessionRepository,
    InMemoryUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock

TEST_PASSWORD_SENTINEL = "TEST_PASSWORD_SENTINEL"
TEST_ACCESS_TOKEN_SENTINEL = "TEST_ACCESS_TOKEN_SENTINEL"
TEST_REFRESH_TOKEN_SENTINEL = "TEST_REFRESH_TOKEN_SENTINEL"


@pytest.fixture
def auth_settings() -> AppSettings:
    return AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=None,
        jwt_secret_key="test-secret-key-with-sufficient-length",
        jwt_algorithm="HS256",
        jwt_access_token_ttl_seconds=3600,
        jwt_refresh_token_ttl_seconds=604800,
        jwt_refresh_absolute_ttl_seconds=7_776_000,
        refresh_token_rotation_enabled=True,
        jwt_issuer="safetymain",
    )


def _assert_no_sentinels(payload: object) -> None:
    serialized = str(payload)
    assert TEST_PASSWORD_SENTINEL not in serialized
    assert TEST_ACCESS_TOKEN_SENTINEL not in serialized
    assert TEST_REFRESH_TOKEN_SENTINEL not in serialized


def test_authentication_sensitive_data_absent_from_persisted_events(
    auth_settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity_store = InMemoryIdentityStore()
    container = create_container(auth_settings, identity_store=identity_store)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email="operator@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    identity_store.register_user(
        user,
        container.password_hasher.hash_password(TEST_PASSWORD_SENTINEL),
    )
    audit_events = InMemoryAuditEventRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()
    captured_logs: list[dict[str, object]] = []

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            audit_events=audit_events,
            refresh_sessions=refresh_sessions,
        )

    def capture_exception(message: str, *args: object, **kwargs: object) -> None:
        captured_logs.append({"message": message, "args": args, "kwargs": kwargs})

    monkeypatch.setattr(
        "backend.core.application.audit.authentication_security_event_recorder.logger.exception",
        capture_exception,
    )

    recorder = AuthenticationSecurityEventRecorder(UtcClock(), uow_factory)
    authenticate = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
        security_event_recorder=recorder,
        uow_factory=uow_factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=auth_settings.jwt_refresh_token_ttl_seconds,
        refresh_absolute_ttl_seconds=auth_settings.jwt_refresh_absolute_ttl_seconds,
    )
    refresh = RefreshAuthenticationHandler(
        token_service=container.token_service,
        security_event_recorder=recorder,
        uow_factory=uow_factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=auth_settings.jwt_refresh_token_ttl_seconds,
    )

    tokens = authenticate.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password=TEST_PASSWORD_SENTINEL,
            audit_context=AuthenticationAuditContext(request_id="sensitive-login"),
        )
    )
    refreshed = refresh.handle(
        RefreshAuthenticationCommand(
            refresh_token=tokens.refresh_token,
            audit_context=AuthenticationAuditContext(request_id="sensitive-refresh"),
        )
    )

    with pytest.raises(InvalidCredentialsError):
        authenticate.handle(
            AuthenticateUserCommand(
                email="operator@example.com",
                password=TEST_PASSWORD_SENTINEL + "-wrong",
                audit_context=AuthenticationAuditContext(request_id="sensitive-fail"),
            )
        )

    with pytest.raises(InvalidRefreshTokenError):
        refresh.handle(
            RefreshAuthenticationCommand(
                refresh_token=TEST_REFRESH_TOKEN_SENTINEL,
                audit_context=AuthenticationAuditContext(request_id="sensitive-bad-refresh"),
            )
        )

    for event in audit_events.snapshot().values():
        _assert_no_sentinels(event.model_dump())
        _assert_no_sentinels(event.metadata)
        assert tokens.access_token not in str(event.model_dump())
        assert tokens.refresh_token not in str(event.model_dump())
        assert refreshed.access_token not in str(event.model_dump())
        assert refreshed.refresh_token not in str(event.model_dump())

    _assert_no_sentinels(captured_logs)


def test_authentication_api_sensitive_data_absent_from_error_responses(
    auth_settings: AppSettings,
) -> None:
    identity_store = InMemoryIdentityStore()
    container = create_container(auth_settings, identity_store=identity_store)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email="operator@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    identity_store.register_user(
        user,
        container.password_hasher.hash_password(TEST_PASSWORD_SENTINEL),
    )
    app = create_app(settings=auth_settings, container=container)
    audit_events = InMemoryAuditEventRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            audit_events=audit_events,
            refresh_sessions=refresh_sessions,
        )

    app.state.container.uow_factory = uow_factory

    with TestClient(app) as client:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "operator@example.com",
                "password": TEST_PASSWORD_SENTINEL,
            },
            headers={"Authorization": f"Bearer {TEST_ACCESS_TOKEN_SENTINEL}"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        failed_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "operator@example.com",
                "password": TEST_PASSWORD_SENTINEL,
            }
            | {"password": f"{TEST_PASSWORD_SENTINEL}-bad"},
        )
        failed_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": TEST_REFRESH_TOKEN_SENTINEL},
            headers={"Authorization": f"Bearer {TEST_ACCESS_TOKEN_SENTINEL}"},
        )

    assert failed_login.status_code == 401
    assert failed_refresh.status_code == 401
    _assert_no_sentinels(failed_login.json())
    _assert_no_sentinels(failed_refresh.json())

    for event in audit_events.snapshot().values():
        dumped = event.model_dump()
        _assert_no_sentinels(dumped)
        assert access_token not in str(dumped)
        assert refresh_token not in str(dumped)
        assert "Authorization" not in str(dumped)
        assert TEST_ACCESS_TOKEN_SENTINEL not in str(dumped)

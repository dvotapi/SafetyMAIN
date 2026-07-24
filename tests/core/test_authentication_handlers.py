from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.audit.authentication_failure_codes import (
    AUTHENTICATION_FORBIDDEN,
    INVALID_CREDENTIALS,
    INVALID_REFRESH_TOKEN,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.logout import LogoutCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.logout import LogoutHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.refresh_session import RefreshTokenIdHash
from backend.core.infrastructure.auth.in_memory_identity_store import (
    InMemoryIdentityStore,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryRefreshTokenSessionRepository,
    InMemoryUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock


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


@pytest.fixture
def identity_store(auth_settings: AppSettings) -> InMemoryIdentityStore:
    store = InMemoryIdentityStore()
    container = create_container(auth_settings, identity_store=store)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email="operator@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    store.register_user(
        user,
        container.password_hasher.hash_password("secret-password"),
    )
    return store


@pytest.fixture
def auth_stack(auth_settings: AppSettings, identity_store: InMemoryIdentityStore):
    container = create_container(auth_settings, identity_store=identity_store)
    audit_events = InMemoryAuditEventRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            audit_events=audit_events,
            refresh_sessions=refresh_sessions,
        )

    container.uow_factory = uow_factory
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
    logout = LogoutHandler(
        token_service=container.token_service,
        security_event_recorder=recorder,
        uow_factory=uow_factory,
        clock=UtcClock(),
    )
    return authenticate, refresh, logout, audit_events, refresh_sessions, container


def _audit_context() -> AuthenticationAuditContext:
    return AuthenticationAuditContext(
        request_id="req-auth-test",
        client_ip="203.0.113.10",
        user_agent="SafetyMAIN-Test/1.0",
    )


def test_authenticate_user_handler_issues_tokens(auth_stack) -> None:
    authenticate_handler, _, _, _, _, _ = auth_stack

    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"
    assert tokens.expires_in == 3600


def test_authenticate_user_handler_records_login_success(auth_stack) -> None:
    authenticate_handler, _, _, audit_events, _, container = auth_stack
    user = container.user_lookup.get_user_by_email("operator@example.com")
    assert user is not None

    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    event = events[0]
    assert event.action is AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED
    assert event.outcome is AuditOutcome.SUCCESS
    assert event.actor_user_id == user.id
    assert event.resource_id == user.id.value
    assert event.metadata["request_id"] == "req-auth-test"
    assert event.metadata["client_ip"] == "203.0.113.10"
    assert event.metadata["authentication_method"] == "password"
    assert "secret-password" not in str(event.model_dump())
    assert tokens.access_token not in str(event.model_dump())
    assert tokens.refresh_token not in str(event.model_dump())


def test_authenticate_user_handler_rejects_invalid_password(auth_stack) -> None:
    authenticate_handler, _, _, audit_events, _, container = auth_stack
    user = container.user_lookup.get_user_by_email("operator@example.com")
    assert user is not None

    with pytest.raises(InvalidCredentialsError):
        authenticate_handler.handle(
            AuthenticateUserCommand(
                email="operator@example.com",
                password="wrong-password",
                audit_context=_audit_context(),
            )
        )

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    event = events[0]
    assert event.action is AuditAction.AUTHENTICATION_LOGIN_FAILED
    assert event.outcome is AuditOutcome.FAILURE
    assert event.failure_code == INVALID_CREDENTIALS
    assert event.actor_user_id == user.id
    assert "wrong-password" not in str(event.model_dump())


def test_authenticate_user_handler_records_unknown_actor_for_unknown_email(
    auth_stack,
) -> None:
    authenticate_handler, _, _, audit_events, _, _ = auth_stack

    with pytest.raises(InvalidCredentialsError):
        authenticate_handler.handle(
            AuthenticateUserCommand(
                email="missing@example.com",
                password="secret-password",
                audit_context=_audit_context(),
            )
        )

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].actor_user_id is None
    assert events[0].failure_code == INVALID_CREDENTIALS


def test_authenticate_user_handler_rejects_suspended_user(
    auth_settings: AppSettings,
    identity_store: InMemoryIdentityStore,
) -> None:
    container = create_container(auth_settings, identity_store=identity_store)
    suspended_user = User(
        id=UserId(value=uuid4()),
        display_name="Suspended Operator",
        email="suspended@example.com",
        status=UserStatus.SUSPENDED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    identity_store.register_user(
        suspended_user,
        container.password_hasher.hash_password("secret-password"),
    )
    audit_events = InMemoryAuditEventRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(audit_events=audit_events)

    handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
        security_event_recorder=AuthenticationSecurityEventRecorder(
            UtcClock(),
            uow_factory,
        ),
        uow_factory=uow_factory,
        clock=UtcClock(),
        refresh_token_ttl_seconds=auth_settings.jwt_refresh_token_ttl_seconds,
        refresh_absolute_ttl_seconds=auth_settings.jwt_refresh_absolute_ttl_seconds,
    )

    with pytest.raises(AuthenticationForbiddenError):
        handler.handle(
            AuthenticateUserCommand(
                email="suspended@example.com",
                password="secret-password",
                audit_context=_audit_context(),
            )
        )

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].failure_code == AUTHENTICATION_FORBIDDEN
    assert events[0].actor_user_id == suspended_user.id


def test_refresh_authentication_handler_rotates_tokens(auth_stack) -> None:
    authenticate_handler, refresh_handler, _, _, _, _ = auth_stack
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )

    refreshed = refresh_handler.handle(
        RefreshAuthenticationCommand(
            refresh_token=tokens.refresh_token,
            audit_context=_audit_context(),
        )
    )

    assert refreshed.access_token
    assert refreshed.refresh_token
    assert refreshed.access_token != tokens.access_token
    assert refreshed.refresh_token != tokens.refresh_token

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(
                refresh_token=tokens.refresh_token,
                audit_context=_audit_context(),
            )
        )


def test_refresh_authentication_handler_records_refresh_success(auth_stack) -> None:
    authenticate_handler, refresh_handler, _, audit_events, _, container = auth_stack
    user = container.user_lookup.get_user_by_email("operator@example.com")
    assert user is not None
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )
    presented_refresh = tokens.refresh_token

    refreshed = refresh_handler.handle(
        RefreshAuthenticationCommand(
            refresh_token=presented_refresh,
            audit_context=_audit_context(),
        )
    )

    events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_SUCCEEDED
    ]
    assert len(events) == 1
    event = events[0]
    assert event.actor_user_id == user.id
    assert event.outcome is AuditOutcome.SUCCESS
    serialized = str(event.model_dump())
    assert presented_refresh not in serialized
    assert refreshed.refresh_token not in serialized
    assert refreshed.access_token not in serialized


def test_refresh_authentication_handler_rejects_invalid_token(auth_stack) -> None:
    _, refresh_handler, _, audit_events, _, _ = auth_stack

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(
                refresh_token="not-a-valid-token",
                audit_context=_audit_context(),
            )
        )

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    event = events[0]
    assert event.action is AuditAction.AUTHENTICATION_REFRESH_FAILED
    assert event.failure_code == INVALID_REFRESH_TOKEN
    assert event.actor_user_id is None
    assert "not-a-valid-token" not in str(event.model_dump())


def test_refresh_reuse_revokes_session_and_records_reuse_event(auth_stack) -> None:
    authenticate_handler, refresh_handler, _, audit_events, refresh_sessions, _ = auth_stack
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )
    original = tokens.refresh_token
    rotated = refresh_handler.handle(
        RefreshAuthenticationCommand(
            refresh_token=original,
            audit_context=_audit_context(),
        )
    )

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(
                refresh_token=original,
                audit_context=_audit_context(),
            )
        )

    reuse_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_REUSE_DETECTED
    ]
    failed_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_FAILED
    ]
    assert len(reuse_events) == 1
    assert failed_events == []

    claims = authenticate_handler._token_service.decode_refresh_token(rotated.refresh_token)
    session = refresh_sessions.get_by_id(claims.session_id)
    assert session is not None
    assert session.is_revoked()

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(
                refresh_token=rotated.refresh_token,
                audit_context=_audit_context(),
            )
        )


def test_logout_revokes_current_session_and_is_idempotent(auth_stack) -> None:
    authenticate_handler, refresh_handler, logout_handler, audit_events, refresh_sessions, _ = (
        auth_stack
    )
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )
    claims = authenticate_handler._token_service.decode_refresh_token(tokens.refresh_token)

    logout_handler.handle(
        LogoutCommand(refresh_token=tokens.refresh_token, audit_context=_audit_context())
    )
    session = refresh_sessions.get_by_id(claims.session_id)
    assert session is not None
    assert session.is_revoked()

    logout_handler.handle(
        LogoutCommand(refresh_token=tokens.refresh_token, audit_context=_audit_context())
    )
    logout_handler.handle(
        LogoutCommand(refresh_token="garbage", audit_context=_audit_context())
    )

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(
                refresh_token=tokens.refresh_token,
                audit_context=_audit_context(),
            )
        )

    logout_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_LOGOUT_SUCCEEDED
    ]
    assert len(logout_events) == 3
    assert hash_refresh_token_jti(claims.jti) not in str(
        [event.model_dump() for event in logout_events]
    )
    assert RefreshTokenIdHash(value=hash_refresh_token_jti(claims.jti)).value not in str(
        tokens.refresh_token
    )


def test_login_creates_persistent_refresh_session(auth_stack) -> None:
    authenticate_handler, _, _, _, refresh_sessions, _ = auth_stack
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
            audit_context=_audit_context(),
        )
    )
    claims = authenticate_handler._token_service.decode_refresh_token(tokens.refresh_token)
    session = refresh_sessions.get_by_id(claims.session_id)
    assert session is not None
    assert session.family_id == claims.family_id
    assert session.current_token_id_hash == RefreshTokenIdHash(
        value=hash_refresh_token_jti(claims.jti)
    )


def test_failed_login_creates_no_refresh_session(auth_stack) -> None:
    authenticate_handler, _, _, _, refresh_sessions, _ = auth_stack
    with pytest.raises(InvalidCredentialsError):
        authenticate_handler.handle(
            AuthenticateUserCommand(
                email="operator@example.com",
                password="wrong-password",
                audit_context=_audit_context(),
            )
        )
    assert refresh_sessions.snapshot()[0] == {}

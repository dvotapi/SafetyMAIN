from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.commands.refresh_authentication import (
    RefreshAuthenticationCommand,
)
from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore


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
def auth_handlers(auth_settings: AppSettings, identity_store: InMemoryIdentityStore):
    container = create_container(auth_settings, identity_store=identity_store)
    return AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    ), RefreshAuthenticationHandler(container.token_service)


def test_authenticate_user_handler_issues_tokens(auth_handlers) -> None:
    authenticate_handler, _ = auth_handlers

    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
        )
    )

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.token_type == "bearer"
    assert tokens.expires_in == 3600


def test_authenticate_user_handler_rejects_invalid_password(auth_handlers) -> None:
    authenticate_handler, _ = auth_handlers

    with pytest.raises(InvalidCredentialsError):
        authenticate_handler.handle(
            AuthenticateUserCommand(
                email="operator@example.com",
                password="wrong-password",
            )
        )


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
    handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )

    with pytest.raises(AuthenticationForbiddenError):
        handler.handle(
            AuthenticateUserCommand(
                email="suspended@example.com",
                password="secret-password",
            )
        )


def test_refresh_authentication_handler_rotates_tokens(auth_handlers) -> None:
    authenticate_handler, refresh_handler = auth_handlers
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
        )
    )

    refreshed = refresh_handler.handle(
        RefreshAuthenticationCommand(refresh_token=tokens.refresh_token)
    )

    assert refreshed.access_token
    assert refreshed.refresh_token
    assert refreshed.access_token != tokens.access_token


def test_refresh_authentication_handler_rejects_invalid_token(auth_handlers) -> None:
    _, refresh_handler = auth_handlers

    with pytest.raises(InvalidRefreshTokenError):
        refresh_handler.handle(
            RefreshAuthenticationCommand(refresh_token="not-a-valid-token")
        )

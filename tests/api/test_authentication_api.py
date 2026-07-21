from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.dependencies import get_security_context
from backend.api.exception_handlers import register_exception_handlers
from backend.api.middleware import RequestIdMiddleware
from backend.api.security import SecurityContext
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from tests.api.contracts.assertions import assert_error_envelope, assert_request_id_header


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
def auth_client(auth_settings: AppSettings) -> tuple[TestClient, str]:
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
        container.password_hasher.hash_password("secret-password"),
    )

    app = create_app(settings=auth_settings, container=container)
    with TestClient(app) as client:
        yield client, "secret-password"


def test_login_returns_token_pair(auth_client: tuple[TestClient, str]) -> None:
    client, password = auth_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )

    assert response.status_code == 200
    assert_request_id_header(response)
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 3600


def test_login_rejects_invalid_credentials(auth_client: tuple[TestClient, str]) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_credentials")


def test_refresh_returns_new_token_pair(auth_client: tuple[TestClient, str]) -> None:
    client, password = auth_client
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_rejects_invalid_token(auth_client: tuple[TestClient, str]) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_refresh_token")


def test_security_dependencies_validate_bearer_token(
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
        container.password_hasher.hash_password("secret-password"),
    )
    handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )
    tokens = handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
        )
    )

    probe_app = FastAPI()
    probe_app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(probe_app)

    @probe_app.get("/probe")
    def probe(security_context: SecurityContext = Depends(get_security_context)) -> dict[str, str]:
        return {"user_id": str(security_context.user_id.value)}

    probe_app.state.settings = auth_settings
    probe_app.state.container = container

    with TestClient(probe_app) as client:
        unauthorized = client.get("/probe")
        assert unauthorized.status_code == 401
        assert_error_envelope(unauthorized, status_code=401, code="unauthenticated")

        authorized = client.get(
            "/probe",
            headers={"Authorization": f"Bearer {tokens.access_token}"},
        )
        assert authorized.status_code == 200
        assert authorized.json()["user_id"] == str(user.id.value)

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
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
from backend.core.application.audit.authentication_failure_codes import (
    AUTHENTICATION_FORBIDDEN,
    EXPIRED_REFRESH_TOKEN,
    INVALID_CREDENTIALS,
    INVALID_REFRESH_TOKEN,
    INVALID_TOKEN_TYPE,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationSecurityEventRecorder,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.role_permissions import permissions_for_role
from backend.core.infrastructure.auth.in_memory_identity_store import (
    InMemoryIdentityStore,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
    InMemoryRefreshTokenSessionRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from backend.core.infrastructure.time.utc_clock import UtcClock
from tests.api.contracts.assertions import (
    assert_error_envelope,
    assert_request_id_header,
)


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


def _wire_audit_store(app: FastAPI) -> InMemoryAuditEventRepository:
    audit_events = InMemoryAuditEventRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            audit_events=audit_events,
            refresh_sessions=refresh_sessions,
        )

    app.state.container.uow_factory = uow_factory
    return audit_events


@pytest.fixture
def auth_client(
    auth_settings: AppSettings,
) -> tuple[TestClient, str, InMemoryAuditEventRepository, UserId]:
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
    audit_events = _wire_audit_store(app)
    with TestClient(app) as client:
        yield client, "secret-password", audit_events, user.id


def test_login_returns_token_pair(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, password, audit_events, user_id = auth_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
        headers={"X-Request-ID": "login-success-req"},
    )

    assert response.status_code == 200
    assert_request_id_header(response)
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 3600

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    event = events[0]
    assert event.action is AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED
    assert event.outcome is AuditOutcome.SUCCESS
    assert event.actor_user_id == user_id
    assert event.metadata["request_id"] == "login-success-req"
    assert event.metadata["authentication_method"] == "password"


def test_login_rejects_invalid_credentials(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, _, audit_events, user_id = auth_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_credentials")

    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].action is AuditAction.AUTHENTICATION_LOGIN_FAILED
    assert events[0].failure_code == INVALID_CREDENTIALS
    assert events[0].actor_user_id == user_id


def test_login_rejects_inactive_user(
    auth_settings: AppSettings,
) -> None:
    identity_store = InMemoryIdentityStore()
    container = create_container(auth_settings, identity_store=identity_store)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Suspended Operator",
        email="suspended@example.com",
        status=UserStatus.SUSPENDED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    identity_store.register_user(
        user,
        container.password_hasher.hash_password("secret-password"),
    )
    app = create_app(settings=auth_settings, container=container)
    audit_events = _wire_audit_store(app)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "suspended@example.com", "password": "secret-password"},
        )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="authentication_forbidden")
    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].failure_code == AUTHENTICATION_FORBIDDEN
    assert events[0].actor_user_id == user.id


def test_refresh_returns_new_token_pair(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, password, audit_events, user_id = auth_client
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"X-Request-ID": "refresh-success-req"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]

    refresh_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_SUCCEEDED
    ]
    assert len(refresh_events) == 1
    assert refresh_events[0].actor_user_id == user_id
    assert refresh_events[0].metadata["request_id"] == "refresh-success-req"


def test_refresh_rejects_invalid_token(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, _, audit_events, _ = auth_client

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_refresh_token")
    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].action is AuditAction.AUTHENTICATION_REFRESH_FAILED
    assert events[0].failure_code == INVALID_REFRESH_TOKEN
    assert events[0].actor_user_id is None


def test_refresh_rejects_expired_token(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
    auth_settings: AppSettings,
) -> None:
    client, _, audit_events, user_id = auth_client
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(user_id.value),
            "typ": "refresh",
            "jti": str(uuid4()),
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "iss": auth_settings.jwt_issuer,
        },
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm,
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_token},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_refresh_token")
    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].failure_code == EXPIRED_REFRESH_TOKEN
    assert events[0].actor_user_id is None


def test_refresh_rejects_wrong_token_type(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
    auth_settings: AppSettings,
) -> None:
    client, password, audit_events, _ = auth_client
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_refresh_token")
    refresh_failures = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_FAILED
    ]
    assert len(refresh_failures) == 1
    assert refresh_failures[0].failure_code == INVALID_TOKEN_TYPE


def test_refresh_rejects_invalid_issuer(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
    auth_settings: AppSettings,
) -> None:
    client, _, audit_events, user_id = auth_client
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(user_id.value),
            "typ": "refresh",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iss": "unexpected-issuer",
        },
        auth_settings.jwt_secret_key,
        algorithm=auth_settings.jwt_algorithm,
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_refresh_token")
    events = list(audit_events.snapshot().values())
    assert len(events) == 1
    assert events[0].failure_code in {
        INVALID_REFRESH_TOKEN,
        "invalid_token_claims",
    }
    assert events[0].actor_user_id is None


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
    audit_events = InMemoryAuditEventRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            audit_events=audit_events,
            refresh_sessions=refresh_sessions,
        )

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


def test_logout_revokes_refresh_session(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, password, audit_events, _ = auth_client
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )
    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"X-Request-ID": "logout-req"},
    )
    assert logout.status_code == 204

    repeated = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert repeated.status_code == 204

    garbage = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "not-a-token"},
    )
    assert garbage.status_code == 204

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 401
    assert_error_envelope(refresh, status_code=401, code="invalid_refresh_token")

    logout_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_LOGOUT_SUCCEEDED
    ]
    assert len(logout_events) >= 1
    assert refresh_token not in str([event.model_dump() for event in logout_events])


def test_refresh_reuse_returns_normalized_error(
    auth_client: tuple[TestClient, str, InMemoryAuditEventRepository, UserId],
) -> None:
    client, password, audit_events, _ = auth_client
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": password},
    )
    original = login.json()["refresh_token"]
    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original},
    )
    assert rotated.status_code == 200

    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original},
    )
    assert reuse.status_code == 401
    assert_error_envelope(reuse, status_code=401, code="invalid_refresh_token")

    reuse_events = [
        event
        for event in audit_events.snapshot().values()
        if event.action is AuditAction.AUTHENTICATION_REFRESH_REUSE_DETECTED
    ]
    assert len(reuse_events) == 1
    assert original not in str(reuse_events[0].model_dump())

    second = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated.json()["refresh_token"]},
    )
    assert second.status_code == 401
    assert_error_envelope(second, status_code=401, code="invalid_refresh_token")


def _build_session_client(
    auth_settings: AppSettings,
) -> tuple[TestClient, str, UserId, OrganizationId, Role]:
    identity_store = InMemoryIdentityStore()
    users = InMemoryUserRepository()
    organizations = InMemoryOrganizationRepository()
    memberships = InMemoryMembershipRepository()
    refresh_sessions = InMemoryRefreshTokenSessionRepository()
    container = create_container(auth_settings, identity_store=identity_store)
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email="operator@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    organization_id = OrganizationId(value=uuid4())
    role = Role.admin()
    identity_store.register_user(
        user,
        container.password_hasher.hash_password("secret-password"),
    )
    users.add(user)
    organizations.add(
        Organization(
            id=organization_id,
            name="Acme Safety",
            status=OrganizationStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    memberships.add(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user.id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=role,
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            users=users,
            organizations=organizations,
            memberships=memberships,
            refresh_sessions=refresh_sessions,
        )

    container.uow_factory = uow_factory
    app = create_app(settings=auth_settings, container=container)
    client = TestClient(app)
    return client, "secret-password", user.id, organization_id, role


def test_session_returns_user_and_memberships(auth_settings: AppSettings) -> None:
    client, password, user_id, organization_id, role = _build_session_client(auth_settings)
    with client:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "operator@example.com", "password": password},
        )
        assert login.status_code == 200

        response = client.get(
            "/api/v1/auth/session",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["user"]["id"] == str(user_id.value)
        assert body["user"]["email"] == "operator@example.com"
        assert body["user"]["display_name"] == "Safety Operator"
        assert body["user"]["status"] == "ACTIVE"
        assert len(body["memberships"]) == 1
        membership = body["memberships"][0]
        assert membership["organization_id"] == str(organization_id.value)
        assert membership["organization_name"] == "Acme Safety"
        assert membership["role"] == role.value
        assert membership["status"] == "ACTIVE"
        assert membership["permissions"] == sorted(
            permission.value for permission in permissions_for_role(role)
        )


def test_session_requires_bearer_token(auth_settings: AppSettings) -> None:
    client, _, _, _, _ = _build_session_client(auth_settings)
    with client:
        response = client.get("/api/v1/auth/session")

        assert response.status_code == 401
        assert_error_envelope(response, status_code=401, code="unauthenticated")

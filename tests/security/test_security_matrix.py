from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import require_permission
from backend.api.exception_handlers import register_exception_handlers
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import RequestIdMiddleware
from backend.api.security import TenantContext
from backend.bootstrap.settings import AppSettings
from backend.core.application.authorization.policies.resource_permissions import (
    KNOWLEDGE_OBJECT_WRITE,
)
from backend.core.application.authorization.role_permission_resolver import (
    RolePermissionResolver,
)
from backend.core.contracts.token_service import TokenValidationError
from backend.core.application.exceptions.authorization import MembershipRequiredError
from backend.core.application.tenant.tenant_context_resolver import TenantContextResolver
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.domain.value_objects.permission import Permission, SystemPermission
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore
from backend.core.infrastructure.auth.jwt_token_service import JwtTokenService
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.knowledge_objects_helpers import create_object, organization_headers
from tests.security.conftest import build_enforced_client


# --- Authentication matrix ---


def test_security_matrix_login_unknown_user(auth_client: tuple[TestClient, str]) -> None:
    client, _ = auth_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "secret-password"},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="invalid_credentials")


def test_security_matrix_login_inactive_user_returns_forbidden(
    auth_settings: AppSettings,
) -> None:
    identity_store = InMemoryIdentityStore()
    from backend.bootstrap.container import create_container

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
    from backend.api.app import create_app

    client = TestClient(create_app(settings=auth_settings, container=container))

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "suspended@example.com", "password": "secret-password"},
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="authentication_forbidden")


def test_security_matrix_refresh_rejects_access_token_as_refresh(
    auth_client: tuple[TestClient, str],
) -> None:
    client, password = auth_client
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


def test_security_matrix_invalid_bearer_token_on_business_route(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, _, _ = build_enforced_client(enforced_auth_settings)

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": "Bearer not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")


def test_security_matrix_expired_access_token_is_rejected() -> None:
    token_service = JwtTokenService(
        secret_key="test-secret-key-with-sufficient-length",
        algorithm="HS256",
        access_token_ttl_seconds=1,
        refresh_token_ttl_seconds=604800,
        issuer="safetymain",
    )
    user_id = UserId(value=uuid4())
    tokens = token_service.issue_tokens(user_id)
    import time

    time.sleep(2)

    with pytest.raises(TokenValidationError):
        token_service.validate_access_token(tokens.access_token)


def test_security_matrix_invalid_signature_is_rejected() -> None:
    token_service = JwtTokenService(
        secret_key="test-secret-key-with-sufficient-length",
        algorithm="HS256",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=604800,
        issuer="safetymain",
    )
    other_service = JwtTokenService(
        secret_key="another-secret-key-with-sufficient-length",
        algorithm="HS256",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=604800,
        issuer="safetymain",
    )
    token = other_service.issue_tokens(UserId(value=uuid4())).access_token

    with pytest.raises(TokenValidationError):
        token_service.validate_access_token(token)


def test_security_matrix_invalid_issuer_is_rejected() -> None:
    token_service = JwtTokenService(
        secret_key="test-secret-key-with-sufficient-length",
        algorithm="HS256",
        access_token_ttl_seconds=3600,
        refresh_token_ttl_seconds=604800,
        issuer="safetymain",
    )
    user_id = UserId(value=uuid4())
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id.value),
        "typ": "access",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + 3600,
        "iss": "wrong-issuer",
    }
    token = jwt.encode(
        payload,
        "test-secret-key-with-sufficient-length",
        algorithm="HS256",
    )

    with pytest.raises(TokenValidationError):
        token_service.validate_access_token(token)


# --- Tenant context matrix ---


def test_security_matrix_matching_token_and_header_organizations(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = build_enforced_client(enforced_auth_settings)

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200


def test_security_matrix_conflicting_token_and_header_organizations(
    enforced_auth_settings: AppSettings,
) -> None:
    identity_store = InMemoryIdentityStore()
    membership_store = InMemoryMembershipStore()
    from backend.bootstrap.container import create_container

    container = create_container(
        enforced_auth_settings,
        identity_store=identity_store,
        membership_store=membership_store,
    )
    user = User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email="operator@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    organization_id = OrganizationId(value=uuid4())
    identity_store.register_user(
        user,
        container.password_hasher.hash_password("secret-password"),
    )
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user.id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.member(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    token_with_org = container.token_service.issue_tokens(
        user.id,
        organization_id=organization_id,
    ).access_token

    from backend.api.app import create_app

    client = TestClient(create_app(settings=enforced_auth_settings, container=container))
    other_org_id = uuid4()

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(other_org_id),
            "Authorization": f"Bearer {token_with_org}",
        },
    )

    assert response.status_code == 422
    assert_error_envelope(response, status_code=422, code="organization_context_required")


def test_security_matrix_sole_active_membership_fallback() -> None:
    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.member(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    resolver = TenantContextResolver(membership_store)

    resolved = resolver.resolve_organization_id(
        user_id=user_id,
        token_organization_id=None,
        header_organization_id=None,
    )

    assert resolved == organization_id


def test_security_matrix_multiple_active_memberships_require_explicit_selection() -> None:
    user_id = UserId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    for _ in range(2):
        membership_store.register_membership(
            Membership(
                id=MembershipId(value=uuid4()),
                user_id=user_id,
                organization_id=OrganizationId(value=uuid4()),
                status=MembershipStatus.ACTIVE,
                role=Role.member(),
                joined_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
    resolver = TenantContextResolver(membership_store)

    with pytest.raises(MembershipRequiredError):
        resolver.resolve_organization_id(
            user_id=user_id,
            token_organization_id=None,
            header_organization_id=None,
        )


# --- Membership matrix ---


def test_security_matrix_inactive_membership_is_rejected(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = build_enforced_client(
        enforced_auth_settings,
        membership_status=MembershipStatus.INVITED,
    )

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")


def test_security_matrix_revoked_membership_is_rejected(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = build_enforced_client(
        enforced_auth_settings,
        membership_status=MembershipStatus.REVOKED,
    )

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")


# --- RBAC matrix ---


def test_security_matrix_admin_has_all_system_permissions() -> None:
    resolver = RolePermissionResolver()
    permissions = resolver.resolve(Role.admin())

    for permission in SystemPermission:
        assert Permission.from_system_permission(permission) in permissions


def test_security_matrix_unknown_role_denies_permission() -> None:
    resolver = RolePermissionResolver()

    permissions = resolver.resolve(Role(value="custom-role"))

    assert permissions == frozenset()


def test_security_matrix_permission_dependency_skips_checks_in_compatibility_mode(
    auth_settings: AppSettings,
) -> None:
    from backend.bootstrap.container import create_container

    compatibility_settings = AppSettings(
        app_name=auth_settings.app_name,
        app_version=auth_settings.app_version,
        app_env=auth_settings.app_env,
        database_url=None,
        jwt_secret_key=auth_settings.jwt_secret_key,
        jwt_algorithm=auth_settings.jwt_algorithm,
        jwt_access_token_ttl_seconds=auth_settings.jwt_access_token_ttl_seconds,
        jwt_refresh_token_ttl_seconds=auth_settings.jwt_refresh_token_ttl_seconds,
        jwt_issuer=auth_settings.jwt_issuer,
        auth_enforcement=False,
    )
    container = create_container(compatibility_settings)
    app = FastAPI()
    app.state.container = container
    app.state.settings = compatibility_settings
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/protected-write")
    def protected_write(
        tenant_context: Annotated[
            TenantContext,
            Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
        ],
    ) -> dict[str, str]:
        return {"organization_id": str(tenant_context.organization_id.value)}

    organization_id = OrganizationId(value=uuid4())
    client = TestClient(app)
    response = client.get(
        "/protected-write",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 200


def test_security_matrix_auditor_denied_write_permission(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    app = FastAPI()
    app.state.container = client.app.state.container
    app.state.settings = enforced_auth_settings
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/protected-write")
    def protected_write(
        tenant_context: Annotated[
            TenantContext,
            Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
        ],
    ) -> dict[str, str]:
        return {"organization_id": str(tenant_context.organization_id.value)}

    probe_client = TestClient(app)
    response = probe_client.get(
        "/protected-write",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_security_matrix_permission_check_without_membership_raises_denied() -> None:
    from backend.core.application.authorization.authorization_service import AuthorizationService
    from backend.core.application.exceptions.authorization import OrganizationAccessDeniedError

    user_id = UserId(value=uuid4())
    organization_id = OrganizationId(value=uuid4())
    membership_store = InMemoryMembershipStore()
    service = AuthorizationService(
        membership_verification=membership_store,
        membership_lookup=membership_store,
    )

    with pytest.raises(OrganizationAccessDeniedError):
        service.require_permission(
            actor_user_id=user_id,
            organization_id=organization_id,
            permission=Permission.from_system_permission(SystemPermission.KNOWLEDGE_OBJECT_READ),
        )


# --- Isolation matrix ---


def test_security_matrix_cross_organization_knowledge_object_masked_with_auth(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, user_id = build_enforced_client(
        enforced_auth_settings
    )
    other_organization_id = OrganizationId(value=uuid4())
    membership_store = client.app.state.container.membership_store
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=other_organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.member(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )

    create_response = client.post(
        "/api/v1/knowledge-objects",
        headers={
            **organization_headers(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "type": "policy",
            "metadata": {"title": "Information Security Policy"},
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()

    response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers={
            ORGANIZATION_ID_HEADER: str(other_organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert_error_envelope(response, status_code=404, code="knowledge_object_not_found")


def test_security_matrix_compatibility_mode_header_only_still_works(
    auth_settings: AppSettings,
) -> None:
    from backend.api.app import create_app
    from backend.bootstrap.container import create_container
    from backend.core.infrastructure.persistence.in_memory import (
        InMemoryKnowledgeObjectRelationRepository,
        InMemoryKnowledgeObjectRepository,
        InMemoryUnitOfWork,
    )

    compatibility_settings = AppSettings(
        app_name=auth_settings.app_name,
        app_version=auth_settings.app_version,
        app_env=auth_settings.app_env,
        database_url=None,
        jwt_secret_key=auth_settings.jwt_secret_key,
        jwt_algorithm=auth_settings.jwt_algorithm,
        jwt_access_token_ttl_seconds=auth_settings.jwt_access_token_ttl_seconds,
        jwt_refresh_token_ttl_seconds=auth_settings.jwt_refresh_token_ttl_seconds,
        jwt_issuer=auth_settings.jwt_issuer,
        auth_enforcement=False,
    )
    container = create_container(compatibility_settings)
    knowledge_objects = InMemoryKnowledgeObjectRepository()
    relations = InMemoryKnowledgeObjectRelationRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=knowledge_objects,
            relations=relations,
        )

    container.uow_factory = uow_factory
    client = TestClient(create_app(settings=compatibility_settings, container=container))
    organization_id = uuid4()

    created = create_object(client, organization_id)

    assert created["id"]

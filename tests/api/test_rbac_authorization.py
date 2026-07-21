from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import require_permission
from backend.api.exception_handlers import register_exception_handlers
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import RequestIdMiddleware
from backend.api.security import TenantContext
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.authorization.policies.resource_permissions import (
    KNOWLEDGE_OBJECT_WRITE,
)
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore
from tests.api.contracts.assertions import assert_error_envelope


@pytest.fixture
def enforced_auth_settings() -> AppSettings:
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
        auth_enforcement=True,
    )


def _build_permission_protected_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[TestClient, OrganizationId, str]:
    identity_store = InMemoryIdentityStore()
    membership_store = InMemoryMembershipStore()
    container = create_container(
        settings,
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
            role=role,
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    authenticate_handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="operator@example.com",
            password="secret-password",
        )
    )

    app = FastAPI()
    app.state.container = container
    app.state.settings = settings
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

    return TestClient(app), organization_id, tokens.access_token


def test_permission_dependency_allows_member_write(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token = _build_permission_protected_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/protected-write",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["organization_id"] == str(organization_id.value)


def test_permission_dependency_denies_auditor_write(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token = _build_permission_protected_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )

    response = client.get(
        "/protected-write",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")

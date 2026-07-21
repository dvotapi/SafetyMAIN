from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.knowledge_objects_helpers import create_object


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


def _build_enforced_client(
    settings: AppSettings,
) -> tuple[TestClient, OrganizationId, str]:
    from backend.core.infrastructure.persistence.in_memory import (
        InMemoryKnowledgeObjectRelationRepository,
        InMemoryKnowledgeObjectRepository,
        InMemoryUnitOfWork,
    )

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

    knowledge_objects = InMemoryKnowledgeObjectRepository()
    relations = InMemoryKnowledgeObjectRelationRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=knowledge_objects,
            relations=relations,
        )

    container.uow_factory = uow_factory
    app = create_app(settings=settings, container=container)
    client = TestClient(app)
    return client, organization_id, tokens.access_token


def test_compatibility_mode_allows_header_only_access(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    created = create_object(client, organization_id)

    assert created["id"]


def test_enforced_mode_requires_authentication(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, _token = _build_enforced_client(enforced_auth_settings)

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")


def test_enforced_mode_allows_member_with_bearer_token(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token = _build_enforced_client(enforced_auth_settings)

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200


def test_enforced_mode_rejects_non_member(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_enforced_client(enforced_auth_settings)
    other_organization_id = uuid4()

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(other_organization_id),
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")

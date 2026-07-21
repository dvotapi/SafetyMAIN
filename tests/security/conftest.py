from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore


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

    with TestClient(create_app(settings=auth_settings, container=container)) as client:
        yield client, "secret-password"


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


def build_enforced_client(
    settings: AppSettings,
    *,
    role: Role = Role.member(),
    membership_status: MembershipStatus = MembershipStatus.ACTIVE,
) -> tuple[TestClient, OrganizationId, str, UserId]:
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
            status=membership_status,
            role=role,
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
    return TestClient(app), organization_id, tokens.access_token, user.id

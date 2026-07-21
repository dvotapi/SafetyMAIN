from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.dependencies import get_uow
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
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)
from tests.api.conftest import FakeUnitOfWork
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.knowledge_objects_helpers import create_object
from tests.api.relations_helpers import create_relation, create_source_and_target
from tests.security.conftest import build_enforced_client


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


def _auth_headers(organization_id: OrganizationId, access_token: str) -> dict[str, str]:
    return {
        ORGANIZATION_ID_HEADER: str(organization_id.value),
        "Authorization": f"Bearer {access_token}",
    }


def _register_user_with_role_in_org(
    client: TestClient,
    organization_id: OrganizationId,
    *,
    role: Role,
    email: str,
    password: str = "secret-password",
) -> str:
    container = client.app.state.container
    user = User(
        id=UserId(value=uuid4()),
        display_name=email.split("@", maxsplit=1)[0].title(),
        email=email,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    container.identity_store.register_user(
        user,
        container.password_hasher.hash_password(password),
    )
    container.membership_store.register_membership(
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
        AuthenticateUserCommand(email=email, password=password)
    )
    return tokens.access_token


def _build_client_with_role(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[TestClient, OrganizationId, str]:
    client, organization_id, access_token, _ = build_enforced_client(settings, role=role)
    return client, organization_id, access_token


def _build_client_without_membership(
    settings: AppSettings,
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
        display_name="Unassigned Operator",
        email="unassigned@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    organization_id = OrganizationId(value=uuid4())
    identity_store.register_user(
        user,
        container.password_hasher.hash_password("secret-password"),
    )
    authenticate_handler = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )
    tokens = authenticate_handler.handle(
        AuthenticateUserCommand(
            email="unassigned@example.com",
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
    return TestClient(create_app(settings=settings, container=container)), organization_id, tokens.access_token


# --- Knowledge Object permission matrix ---


@pytest.mark.parametrize(
    ("method", "path_factory", "json_body"),
    [
        ("get", lambda org_id: "/api/v1/knowledge-objects", None),
        ("post", lambda org_id: "/api/v1/knowledge-objects", {"type": "policy", "metadata": {"title": "Read probe"}}),
    ],
)
def test_admin_knowledge_object_operations_allowed(
    enforced_auth_settings: AppSettings,
    method: str,
    path_factory,
    json_body: dict[str, object] | None,
) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)
    path = path_factory(organization_id)

    if method == "get":
        response = client.get(path, headers=headers)
    else:
        response = client.post(path, headers=headers, json=json_body)

    assert response.status_code in {200, 201}


def test_admin_knowledge_object_delete_allowed(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.admin(),
    )
    created = create_object(
        client,
        organization_id.value,
        headers=_auth_headers(organization_id, access_token),
    )

    response = client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 204


def test_auditor_knowledge_object_read_allowed(enforced_auth_settings: AppSettings) -> None:
    member_client, organization_id, member_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    created = create_object(
        member_client,
        organization_id.value,
        headers=_auth_headers(organization_id, member_token),
    )
    auditor_token = _register_user_with_role_in_org(
        member_client,
        organization_id,
        role=Role.auditor(),
        email="auditor-read@example.com",
    )

    response = member_client.get(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=_auth_headers(organization_id, auditor_token),
    )

    assert response.status_code == 200


def test_auditor_knowledge_object_write_denied(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.auditor(),
    )

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
        json={"type": "policy", "metadata": {"title": "Denied"}},
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_auditor_knowledge_object_delete_denied(enforced_auth_settings: AppSettings) -> None:
    member_client, organization_id, member_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    created = create_object(
        member_client,
        organization_id.value,
        headers=_auth_headers(organization_id, member_token),
    )
    auditor_token = _register_user_with_role_in_org(
        member_client,
        organization_id,
        role=Role.auditor(),
        email="auditor-delete@example.com",
    )

    response = member_client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=_auth_headers(organization_id, auditor_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_member_knowledge_object_write_allowed(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
        json={"type": "policy", "metadata": {"title": "Member write"}},
    )

    assert response.status_code == 201


def test_user_without_membership_denied(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_without_membership(
        enforced_auth_settings
    )

    response = client.get(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")


def test_cross_organization_knowledge_object_masked_after_authorization(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, user_id = build_enforced_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    other_organization_id = OrganizationId(value=uuid4())
    membership_store = client.app.state.container.membership_store
    membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=user_id,
            organization_id=other_organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.admin(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    created = create_object(
        client,
        organization_id.value,
        headers=_auth_headers(organization_id, access_token),
    )

    response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=_auth_headers(other_organization_id, access_token),
    )

    assert response.status_code == 404
    assert_error_envelope(response, status_code=404, code="knowledge_object_not_found")


# --- Relation permission matrix ---


def test_admin_relation_mutations_allowed(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = _auth_headers(organization_id, access_token)
    source, target = create_source_and_target(
        client,
        organization_id.value,
        headers=headers,
    )
    relation = create_relation(
        client,
        organization_id.value,
        source_object_id=source["id"],
        target_object_id=target["id"],
        headers=headers,
    )

    get_response = client.get(
        f"/api/v1/relations/{relation['id']}",
        headers=headers,
    )
    delete_response = client.delete(
        f"/api/v1/relations/{relation['id']}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert delete_response.status_code == 204


def test_auditor_relation_read_denied_without_relation_manage(
    enforced_auth_settings: AppSettings,
) -> None:
    member_client, organization_id, member_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _auth_headers(organization_id, member_token)
    source, target = create_source_and_target(
        member_client,
        organization_id.value,
        headers=headers,
    )
    relation = create_relation(
        member_client,
        organization_id.value,
        source_object_id=source["id"],
        target_object_id=target["id"],
        headers=headers,
    )
    auditor_token = _register_user_with_role_in_org(
        member_client,
        organization_id,
        role=Role.auditor(),
        email="auditor-relation-read@example.com",
    )

    response = member_client.get(
        f"/api/v1/relations/{relation['id']}",
        headers=_auth_headers(organization_id, auditor_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_auditor_relation_mutation_denied(enforced_auth_settings: AppSettings) -> None:
    member_client, organization_id, member_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _auth_headers(organization_id, member_token)
    source, target = create_source_and_target(
        member_client,
        organization_id.value,
        headers=headers,
    )
    auditor_token = _register_user_with_role_in_org(
        member_client,
        organization_id,
        role=Role.auditor(),
        email="auditor-relation-write@example.com",
    )

    response = member_client.post(
        "/api/v1/relations",
        headers=_auth_headers(organization_id, auditor_token),
        json={
            "source_object_id": source["id"],
            "target_object_id": target["id"],
            "type": "references",
        },
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_member_relation_operations_allowed(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _auth_headers(organization_id, access_token)
    source, target = create_source_and_target(client, organization_id.value, headers=headers)

    response = client.post(
        "/api/v1/relations",
        headers=headers,
        json={
            "source_object_id": source["id"],
            "target_object_id": target["id"],
            "type": "references",
        },
    )

    assert response.status_code == 201


def test_traversal_requires_relation_read_permission(
    enforced_auth_settings: AppSettings,
) -> None:
    member_client, organization_id, member_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    headers = _auth_headers(organization_id, member_token)
    source, target = create_source_and_target(
        member_client,
        organization_id.value,
        headers=headers,
    )
    create_relation(
        member_client,
        organization_id.value,
        source_object_id=source["id"],
        target_object_id=target["id"],
        headers=headers,
    )
    auditor_token = _register_user_with_role_in_org(
        member_client,
        organization_id,
        role=Role.auditor(),
        email="auditor-traversal@example.com",
    )

    response = member_client.get(
        f"/api/v1/knowledge-objects/{source['id']}/relations/outgoing",
        headers=_auth_headers(organization_id, auditor_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


# --- Authentication state ---


def test_missing_bearer_token_rejected(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, _, _ = build_enforced_client(enforced_auth_settings)

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")


def test_malformed_bearer_token_rejected(enforced_auth_settings: AppSettings) -> None:
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


def test_refresh_token_cannot_authorize_business_route(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, _, _ = build_enforced_client(enforced_auth_settings)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "operator@example.com", "password": "secret-password"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.get(
        "/api/v1/knowledge-objects",
        headers={
            ORGANIZATION_ID_HEADER: str(organization_id.value),
            "Authorization": f"Bearer {refresh_token}",
        },
    )

    assert response.status_code == 401
    assert_error_envelope(response, status_code=401, code="unauthenticated")


def test_unknown_role_denied(enforced_auth_settings: AppSettings) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role(value="custom-role"),
    )

    response = client.get(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")


def test_handler_not_executed_after_permission_denied(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token = _build_client_with_role(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    FakeUnitOfWork.instances.clear()

    def _fake_uow():
        with FakeUnitOfWork() as uow:
            yield uow

    client.app.dependency_overrides[get_uow] = _fake_uow

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
        json={"type": "policy", "metadata": {"title": "Should not persist"}},
    )

    assert response.status_code == 403
    assert FakeUnitOfWork.instances == []

    client.app.dependency_overrides.clear()


# --- Compatibility mode ---


def test_compatibility_mode_anonymous_header_access(
    enforced_auth_settings: AppSettings,
) -> None:
    compatibility_settings = AppSettings(
        app_name=enforced_auth_settings.app_name,
        app_version=enforced_auth_settings.app_version,
        app_env=enforced_auth_settings.app_env,
        database_url=None,
        jwt_secret_key=enforced_auth_settings.jwt_secret_key,
        jwt_algorithm=enforced_auth_settings.jwt_algorithm,
        jwt_access_token_ttl_seconds=enforced_auth_settings.jwt_access_token_ttl_seconds,
        jwt_refresh_token_ttl_seconds=enforced_auth_settings.jwt_refresh_token_ttl_seconds,
        jwt_issuer=enforced_auth_settings.jwt_issuer,
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

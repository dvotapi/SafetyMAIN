from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId, Role, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_list_criteria import AuditEventListCriteria
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)
from tests.api.contracts.assertions import assert_error_envelope
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


def _build_admin_audit_client(
    settings: AppSettings,
    *,
    role: Role,
) -> tuple[TestClient, OrganizationId, str, InMemoryAuditEventRepository, UserId]:
    audit_events = InMemoryAuditEventRepository()
    users = InMemoryUserRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            users=users,
            audit_events=audit_events,
        )

    client, organization_id, access_token, actor_user_id = build_enforced_client(
        settings,
        role=role,
    )
    client.app.state.container.uow_factory = uow_factory
    return client, organization_id, access_token, audit_events, actor_user_id


def _list_permission_denials(
    audit_events: InMemoryAuditEventRepository,
    scope_organization_id: OrganizationId,
) -> tuple[AuditEvent, ...]:
    result = audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=scope_organization_id,
            offset=0,
            limit=50,
            action=AuditAction.AUTHORIZATION_PERMISSION_DENIED,
            outcome=AuditOutcome.FAILURE,
        )
    )
    return result.items


@pytest.mark.parametrize(
    ("role", "method", "path"),
    [
        (Role.auditor(), "POST", "/api/v1/admin/users"),
        (Role.auditor(), "POST", "/api/v1/admin/organizations"),
        (Role.auditor(), "POST", "/api/v1/admin/memberships"),
        (Role.auditor(), "POST", "/api/v1/admin/invitations"),
        (Role.member(), "GET", "/api/v1/admin/users"),
        (Role.member(), "GET", "/api/v1/admin/memberships"),
        (Role.member(), "GET", "/api/v1/admin/audit-events"),
    ],
)
def test_administrative_permission_denial_creates_one_audit_event(
    enforced_auth_settings: AppSettings,
    role: Role,
    method: str,
    path: str,
) -> None:
    client, organization_id, access_token, audit_events, actor_user_id = _build_admin_audit_client(
        enforced_auth_settings,
        role=role,
    )
    headers = _auth_headers(organization_id, access_token)
    json_body = {"email": "blocked@example.com", "display_name": "Blocked"} if method == "POST" else None

    response = client.request(method, path, headers=headers, json=json_body)

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")

    events = _list_permission_denials(audit_events, organization_id)
    assert len(events) == 1
    event = events[0]
    assert event.actor_user_id == actor_user_id
    assert event.authorization_organization_id == organization_id
    assert event.failure_code == "permission_denied"
    assert "required_permission" in event.metadata
    assert event.metadata["http_method"] == method
    assert event.metadata["route_template"].startswith("/api/v1/admin/")
    assert "Bearer" not in str(event.metadata)
    assert "Authorization" not in str(event.metadata)


def test_unknown_role_administrative_denial_is_audited(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role(value="unknown"),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert len(_list_permission_denials(audit_events, organization_id)) == 1


def test_business_permission_denial_does_not_create_administrative_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    audit_events = InMemoryAuditEventRepository()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(
            knowledge_objects=InMemoryKnowledgeObjectRepository(),
            relations=InMemoryKnowledgeObjectRelationRepository(),
            audit_events=audit_events,
        )

    client, organization_id, access_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.auditor(),
    )
    client.app.state.container.uow_factory = uow_factory

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=_auth_headers(organization_id, access_token),
        json={
            "title": "Blocked",
            "content": "Blocked content",
            "metadata": {},
        },
    )

    assert response.status_code == 403
    assert (
        audit_events.list_events(
            AuditEventListCriteria(
                scope_organization_id=organization_id,
                offset=0,
                limit=10,
            )
        ).total
        == 0
    )


def test_missing_token_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    audit_events = InMemoryAuditEventRepository()
    client, organization_id, _, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    client.app.state.container.uow_factory = lambda: InMemoryUnitOfWork(
        audit_events=audit_events
    )

    response = client.get(
        "/api/v1/admin/users",
        headers={ORGANIZATION_ID_HEADER: str(organization_id.value)},
    )

    assert response.status_code == 401
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_permission_denial_audit_persistence_failure_still_returns_403(
    enforced_auth_settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    container = client.app.state.container
    original_factory = container.uow_factory

    def failing_factory() -> InMemoryUnitOfWork:
        uow = original_factory()

        class BrokenAuditRepo:
            def add(self, event: object) -> None:
                raise RuntimeError("permission denial audit persistence failed")

            def get(self, audit_event_id: object) -> AuditEvent:
                raise NotImplementedError

            def list_events(self, criteria: object) -> object:
                raise NotImplementedError

        uow._audit_events = BrokenAuditRepo()  # type: ignore[attr-defined]
        return uow

    container.uow_factory = failing_factory
    mock_logger = MagicMock()
    monkeypatch.setattr(
        "backend.core.application.audit.administrative_audit_recorder.logger",
        mock_logger,
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="permission_denied")
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0
    assert mock_logger.exception.called


def test_compatibility_mode_does_not_create_permission_denial_audit_event() -> None:
    audit_events = InMemoryAuditEventRepository()
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=None,
        jwt_secret_key="test-secret-key-with-sufficient-length",
        jwt_algorithm="HS256",
        jwt_access_token_ttl_seconds=3600,
        jwt_refresh_token_ttl_seconds=604800,
        jwt_issuer="safetymain",
        auth_enforcement=False,
    )
    client, organization_id, access_token, _ = build_enforced_client(
        settings,
        role=Role.member(),
    )
    client.app.state.container.uow_factory = lambda: InMemoryUnitOfWork(
        audit_events=audit_events
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 200
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_permission_granted_does_not_create_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 200
    assert len(_list_permission_denials(audit_events, organization_id)) == 0


def test_denied_request_does_not_invoke_protected_handler(
    enforced_auth_settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.core.application.handlers.list_users import ListUsersHandler

    def forbidden_handle(self, command: object) -> object:
        raise AssertionError("Protected handler must not run after permission denial.")

    monkeypatch.setattr(ListUsersHandler, "handle", forbidden_handle)

    client, organization_id, access_token, _, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403


def test_exactly_one_record_permission_denial_call_per_denied_request(
    enforced_auth_settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.core.application.audit.administrative_audit_recorder import (
        AdministrativeAuditRecorder,
    )

    call_count = 0
    original = AdministrativeAuditRecorder.record_permission_denial

    def counting_record_permission_denial(
        self: AdministrativeAuditRecorder,
        spec: object,
    ) -> None:
        nonlocal call_count
        call_count += 1
        original(self, spec)

    monkeypatch.setattr(
        AdministrativeAuditRecorder,
        "record_permission_denial",
        counting_record_permission_denial,
    )

    client, organization_id, access_token, _, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert call_count == 1


def test_denied_request_appends_exactly_one_audit_event(
    enforced_auth_settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    append_count = 0
    original_add = InMemoryAuditEventRepository.add

    def counting_add(
        self: InMemoryAuditEventRepository,
        event: AuditEvent,
    ) -> None:
        nonlocal append_count
        append_count += 1
        original_add(self, event)

    monkeypatch.setattr(InMemoryAuditEventRepository, "add", counting_add)

    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert append_count == 1
    assert len(_list_permission_denials(audit_events, organization_id)) == 1


@pytest.mark.parametrize(
    "authorization_header",
    [
        None,
        "NotBearer token",
        "Bearer not-a-valid-token",
    ],
)
def test_authentication_failures_do_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
    authorization_header: str | None,
) -> None:
    client, organization_id, _, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    headers = {ORGANIZATION_ID_HEADER: str(organization_id.value)}
    if authorization_header is not None:
        headers["Authorization"] = authorization_header

    response = client.get("/api/v1/admin/users", headers=headers)

    assert response.status_code == 401
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_expired_token_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    import jwt

    client, organization_id, _, audit_events, actor_user_id = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(actor_user_id.value),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()) - 7200,
            "exp": int(now.timestamp()) - 3600,
            "iss": enforced_auth_settings.jwt_issuer,
        },
        enforced_auth_settings.jwt_secret_key,
        algorithm=enforced_auth_settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, expired_token),
    )

    assert response.status_code == 401
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_invalid_issuer_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    import jwt

    client, organization_id, _, audit_events, actor_user_id = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    now = datetime.now(UTC)
    invalid_token = jwt.encode(
        {
            "sub": str(actor_user_id.value),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(now.timestamp()) + 3600,
            "iss": "wrong-issuer",
        },
        enforced_auth_settings.jwt_secret_key,
        algorithm=enforced_auth_settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, invalid_token),
    )

    assert response.status_code == 401
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_organization_context_mismatch_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    from backend.api.app import create_app
    from backend.bootstrap.container import create_container
    from backend.core.domain.entities.membership import Membership, MembershipStatus
    from backend.core.domain.entities.user import User, UserStatus
    from backend.core.domain.value_objects import MembershipId
    from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
    from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore

    audit_events = InMemoryAuditEventRepository()
    identity_store = InMemoryIdentityStore()
    membership_store = InMemoryMembershipStore()
    container = create_container(
        enforced_auth_settings,
        identity_store=identity_store,
        membership_store=membership_store,
    )
    user = User(
        id=UserId(value=uuid4()),
        display_name="Mismatch User",
        email="mismatch@example.com",
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
    container.uow_factory = lambda: InMemoryUnitOfWork(audit_events=audit_events)
    client = TestClient(create_app(settings=enforced_auth_settings, container=container))

    response = client.get(
        "/api/v1/admin/users",
        headers={
            ORGANIZATION_ID_HEADER: str(uuid4()),
            "Authorization": f"Bearer {token_with_org}",
        },
    )

    assert response.status_code == 422
    assert_error_envelope(response, status_code=422, code="organization_context_required")
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_missing_membership_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.admin(),
    )
    other_organization_id = OrganizationId(value=uuid4())

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(other_organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_inactive_membership_does_not_create_permission_denial_audit_event(
    enforced_auth_settings: AppSettings,
) -> None:
    from backend.core.domain.entities.membership import MembershipStatus

    audit_events = InMemoryAuditEventRepository()
    client, organization_id, access_token, _ = build_enforced_client(
        enforced_auth_settings,
        role=Role.admin(),
        membership_status=MembershipStatus.INVITED,
    )
    client.app.state.container.uow_factory = lambda: InMemoryUnitOfWork(
        audit_events=audit_events
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, access_token),
    )

    assert response.status_code == 403
    assert_error_envelope(response, status_code=403, code="organization_access_denied")
    assert audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=organization_id,
            offset=0,
            limit=10,
        )
    ).total == 0


def test_permission_denial_event_visible_through_audit_api(
    enforced_auth_settings: AppSettings,
) -> None:
    from backend.core.application.commands.authenticate_user import AuthenticateUserCommand
    from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
    from backend.core.domain.entities.membership import Membership, MembershipStatus
    from backend.core.domain.entities.user import User, UserStatus
    from backend.core.domain.value_objects import MembershipId
    from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
    from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore

    client, organization_id, member_token, audit_events, member_user_id = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    container = client.app.state.container
    assert isinstance(container.identity_store, InMemoryIdentityStore)
    assert isinstance(container.membership_store, InMemoryMembershipStore)

    admin_user = User(
        id=UserId(value=uuid4()),
        display_name="Audit Reader",
        email="audit-reader@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    container.identity_store.register_user(
        admin_user,
        container.password_hasher.hash_password("audit-reader-password"),
    )
    container.membership_store.register_membership(
        Membership(
            id=MembershipId(value=uuid4()),
            user_id=admin_user.id,
            organization_id=organization_id,
            status=MembershipStatus.ACTIVE,
            role=Role.admin(),
            joined_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    admin_token = AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    ).handle(
        AuthenticateUserCommand(
            email="audit-reader@example.com",
            password="audit-reader-password",
        )
    ).access_token

    denial_response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, member_token),
    )
    assert denial_response.status_code == 403

    events = _list_permission_denials(audit_events, organization_id)
    assert len(events) == 1
    event = events[0]

    list_response = client.get(
        "/api/v1/admin/audit-events",
        headers=_auth_headers(organization_id, admin_token),
        params={
            "action": AuditAction.AUTHORIZATION_PERMISSION_DENIED.value,
            "outcome": AuditOutcome.FAILURE.value,
            "actor_user_id": str(member_user_id.value),
        },
    )
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["id"] == str(event.id.value)
    assert body["items"][0]["action"] == AuditAction.AUTHORIZATION_PERMISSION_DENIED.value
    assert body["items"][0]["failure_code"] == "permission_denied"

    get_response = client.get(
        f"/api/v1/admin/audit-events/{event.id.value}",
        headers=_auth_headers(organization_id, admin_token),
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(event.id.value)


def test_permission_denial_audit_event_excludes_sensitive_data(
    enforced_auth_settings: AppSettings,
) -> None:
    client, organization_id, access_token, audit_events, _ = _build_admin_audit_client(
        enforced_auth_settings,
        role=Role.member(),
    )
    sensitive_token = access_token

    response = client.get(
        "/api/v1/admin/users",
        headers=_auth_headers(organization_id, sensitive_token),
    )

    assert response.status_code == 403
    assert sensitive_token not in response.text

    events = _list_permission_denials(audit_events, organization_id)
    assert len(events) == 1
    serialized = str(events[0].model_dump())
    assert sensitive_token not in serialized
    assert "Bearer" not in serialized
    assert "Authorization" not in serialized
    assert "secret-password" not in serialized

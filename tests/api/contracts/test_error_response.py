from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api.error_codes import (
    INTERNAL_SERVER_ERROR,
    KNOWLEDGE_OBJECT_ALREADY_ARCHIVED,
    KNOWLEDGE_OBJECT_NOT_FOUND,
)
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.knowledge_objects_helpers import create_object, organization_headers


def test_domain_errors_use_common_envelope(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    not_found = client.get(
        f"/api/v1/knowledge-objects/{uuid4()}",
        headers=organization_headers(organization_id),
    )
    assert_error_envelope(
        not_found,
        status_code=404,
        code=KNOWLEDGE_OBJECT_NOT_FOUND,
    )
    assert not_found.json()["error"]["message"] == "Knowledge Object was not found."


def test_conflict_errors_use_common_envelope(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    duplicate_archive = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/archive",
        headers=organization_headers(organization_id),
    )
    assert duplicate_archive.status_code == 200

    conflict = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/archive",
        headers=organization_headers(organization_id),
    )
    assert_error_envelope(
        conflict,
        status_code=409,
        code=KNOWLEDGE_OBJECT_ALREADY_ARCHIVED,
    )


def test_readiness_error_uses_common_envelope(client: TestClient) -> None:
    from backend.api.dependencies import get_readiness_check

    def failing_readiness_check() -> None:
        raise RuntimeError("db unavailable")

    client.app.dependency_overrides[get_readiness_check] = lambda: failing_readiness_check

    response = client.get("/api/v1/ready")
    assert_error_envelope(response, status_code=503, code="service_not_ready")

    client.app.dependency_overrides.clear()


def test_unexpected_error_uses_common_envelope(app_settings) -> None:
    from backend.api.app import create_app

    application = create_app(settings=app_settings)

    @application.get("/_test/boom")
    def boom() -> None:
        raise RuntimeError("secret internals")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/_test/boom")

    body = assert_error_envelope(
        response,
        status_code=500,
        code=INTERNAL_SERVER_ERROR,
    )
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "secret internals" not in response.text

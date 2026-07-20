from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.error_codes import REQUEST_VALIDATION_ERROR
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import REQUEST_ID_HEADER
from backend.bootstrap.settings import AppSettings
from tests.api.contracts.assertions import assert_error_envelope, assert_request_id_header


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("GET", "/api/v1/health", None),
        ("GET", "/api/v1/ready", None),
    ],
)
def test_system_endpoints_include_request_id(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, object] | None,
) -> None:
    response = client.request(method, path, json=json_body)
    assert response.status_code == 200
    assert_request_id_header(response)


@pytest.mark.parametrize(
    ("method", "path", "json_body", "headers"),
    [
        ("POST", "/api/v1/knowledge-objects", {"type": "   ", "metadata": {}}, None),
        ("GET", "/api/v1/knowledge-objects", None, None),
        (
            "GET",
            "/api/v1/knowledge-objects/not-a-uuid",
            None,
            {"X-Organization-ID": "00000000-0000-0000-0000-000000000001"},
        ),
        ("POST", "/api/v1/relations", {}, None),
    ],
)
def test_business_validation_errors_include_request_id(
    knowledge_object_client: tuple[TestClient, object, object],
    method: str,
    path: str,
    json_body: dict[str, object] | None,
    headers: dict[str, str] | None,
) -> None:
    client, _repository, _organization_id = knowledge_object_client
    response = client.request(method, path, headers=headers, json=json_body)
    assert response.status_code == 422
    body = assert_error_envelope(
        response,
        status_code=422,
        code=REQUEST_VALIDATION_ERROR,
    )
    assert_request_id_header(response)
    assert body["error"]["details"]["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_client_request_id_is_preserved(client: TestClient) -> None:
    custom_request_id = "client-req-001"
    response = client.get(
        "/api/v1/health",
        headers={REQUEST_ID_HEADER: custom_request_id},
    )
    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == custom_request_id


def test_invalid_request_id_is_replaced(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    with TestClient(application) as client:
        response = client.get(
            "/api/v1/health",
            headers={REQUEST_ID_HEADER: "invalid id with spaces"},
        )
    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] != "invalid id with spaces"


def test_missing_organization_header_returns_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-objects")
    assert response.status_code == 422
    assert_error_envelope(response, status_code=422, code=REQUEST_VALIDATION_ERROR)
    assert_request_id_header(response)


def test_missing_organization_header_uses_header_location(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-objects")
    body = response.json()
    violations = body["error"]["details"]["violations"]
    assert any(
        violation["location"] == ["header", ORGANIZATION_ID_HEADER]
        for violation in violations
    )

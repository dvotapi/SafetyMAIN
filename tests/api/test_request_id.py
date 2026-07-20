from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import get_readiness_check
from backend.api.middleware import REQUEST_ID_HEADER, normalize_request_id


def test_provided_request_id_is_echoed(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={REQUEST_ID_HEADER: "client-request-1"},
    )
    assert response.headers[REQUEST_ID_HEADER] == "client-request-1"


def test_missing_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) > 0


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health",
        headers={REQUEST_ID_HEADER: "bad request id with spaces!!!"},
    )
    assert response.headers[REQUEST_ID_HEADER] != "bad request id with spaces!!!"
    assert " " not in response.headers[REQUEST_ID_HEADER]


def test_excessively_long_request_id_is_replaced(client: TestClient) -> None:
    oversized = "a" * 200
    response = client.get(
        "/api/v1/health",
        headers={REQUEST_ID_HEADER: oversized},
    )
    assert response.headers[REQUEST_ID_HEADER] != oversized
    assert len(response.headers[REQUEST_ID_HEADER]) <= 128


def test_error_response_includes_request_id_header(
    app: FastAPI,
    client: TestClient,
) -> None:
    app.dependency_overrides[get_readiness_check] = lambda: (
        lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    response = client.get(
        "/api/v1/ready",
        headers={REQUEST_ID_HEADER: "error-req-42"},
    )
    assert response.status_code == 503
    assert response.headers[REQUEST_ID_HEADER] == "error-req-42"
    assert response.json()["error"]["details"]["request_id"] == "error-req-42"


def test_normalize_request_id_helpers() -> None:
    assert normalize_request_id("valid-id_1.2") == "valid-id_1.2"
    generated = normalize_request_id(None)
    assert generated
    assert normalize_request_id("not valid") != "not valid"

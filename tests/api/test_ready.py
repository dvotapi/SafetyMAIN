from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import get_readiness_check
from backend.api.error_codes import SERVICE_NOT_READY
from backend.api.middleware import REQUEST_ID_HEADER


def test_ready_success_with_injected_check(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_failure_returns_503_without_raw_error(
    app: FastAPI,
    client: TestClient,
) -> None:
    def failing_check() -> None:
        raise RuntimeError("psycopg connection refused secret=super-secret")

    app.dependency_overrides[get_readiness_check] = lambda: failing_check

    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body == {
        "error": {
            "code": SERVICE_NOT_READY,
            "message": "The service is not ready.",
            "details": {"request_id": body["error"]["details"]["request_id"]},
        }
    }
    assert "psycopg" not in response.text
    assert "super-secret" not in response.text
    assert "connection refused" not in response.text
    assert REQUEST_ID_HEADER in response.headers

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.middleware import REQUEST_ID_HEADER
from tests.api.conftest import FakeUnitOfWork


def test_health_returns_ok_schema(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SafetyMAIN API",
        "version": "0.1.0",
    }


def test_health_includes_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert REQUEST_ID_HEADER in response.headers
    assert response.headers[REQUEST_ID_HEADER]


def test_health_does_not_use_uow_or_readiness(client: TestClient) -> None:
    FakeUnitOfWork.instances.clear()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert FakeUnitOfWork.instances == []
    assert "database" not in response.text.lower()
    assert "postgresql" not in response.text.lower()

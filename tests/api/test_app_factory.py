from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.bootstrap.settings import AppSettings


def test_create_app_returns_fastapi_instance(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    assert isinstance(application, FastAPI)


def test_application_metadata(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    assert application.title == "SafetyMAIN API"
    assert application.version == "0.1.0"
    assert application.docs_url == "/docs"
    assert application.openapi_url == "/openapi.json"


def test_application_creation_has_no_database_side_effects(
    app_settings: AppSettings,
) -> None:
    application = create_app(settings=app_settings)
    assert application.state.container.engine is None
    assert application.state.container.session_factory is None


def test_openapi_and_docs_available(client: TestClient) -> None:
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    assert "openapi" in openapi_response.json()

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200


def test_lifespan_shutdown_without_postgresql(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    with TestClient(application) as test_client:
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

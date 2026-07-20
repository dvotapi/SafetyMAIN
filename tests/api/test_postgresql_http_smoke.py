from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.error_codes import SERVICE_NOT_READY
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import AppSettings
from tests.api.knowledge_objects_helpers import organization_headers

pytestmark = pytest.mark.db
pytest_plugins = ("tests.infrastructure.db_fixtures",)


@pytest.fixture(scope="module")
def migrated_database(database_url: str) -> Iterator[None]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest.fixture(scope="module")
def postgres_client(
    database_url: str,
    migrated_database: None,
) -> Iterator[TestClient]:
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url=database_url,
        cors_allowed_origins=(),
    )
    container = create_container(settings)
    application = create_app(settings=settings, container=container)
    with TestClient(application) as client:
        yield client
    container.dispose()


@pytest.fixture(scope="module")
def organization_id() -> UUID:
    return uuid4()


def test_readiness_success_against_live_postgresql(postgres_client: TestClient) -> None:
    response = postgres_client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_failure_when_database_unavailable(database_url: str) -> None:
    settings = AppSettings(
        app_name="SafetyMAIN API",
        app_version="0.1.0",
        app_env="test",
        database_url="postgresql+psycopg://safetymain:safetymain@localhost:5439/safetymain",
        cors_allowed_origins=(),
    )
    container = create_container(settings)
    application = create_app(settings=settings, container=container)
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == SERVICE_NOT_READY
    assert body["error"]["message"] == "The service is not ready."
    assert "5439" not in response.text
    container.dispose()


def test_knowledge_object_http_smoke_against_postgresql(
    postgres_client: TestClient,
    organization_id: UUID,
) -> None:
    headers = organization_headers(organization_id)
    metadata = {
        "title": "PostgreSQL Smoke Policy",
        "enabled": True,
        "count": 3,
        "ratio": 1.5,
        "nested": {"values": [1, False, None]},
    }

    create_response = postgres_client.post(
        "/api/v1/knowledge-objects",
        headers=headers,
        json={"type": "policy", "metadata": metadata},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    object_id = created["id"]
    assert created["metadata"] == metadata

    get_response = postgres_client.get(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["metadata"] == metadata

    updated_metadata = {**metadata, "title": "Updated PostgreSQL Smoke Policy", "count": 4}
    update_response = postgres_client.put(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
        json={"version": 1, "metadata": updated_metadata},
    )
    assert update_response.status_code == 200
    assert update_response.json()["version"] == 2

    history_response = postgres_client.get(
        f"/api/v1/knowledge-objects/{object_id}/history",
        headers=headers,
    )
    assert history_response.status_code == 200
    assert history_response.json()["items"][0]["metadata"] == metadata

    archive_response = postgres_client.post(
        f"/api/v1/knowledge-objects/{object_id}/archive",
        headers=headers,
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    restore_response = postgres_client.post(
        f"/api/v1/knowledge-objects/{object_id}/restore",
        headers=headers,
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "active"

    delete_response = postgres_client.delete(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204
    assert delete_response.content == b""


def test_relation_and_search_http_smoke_against_postgresql(
    postgres_client: TestClient,
    organization_id: UUID,
) -> None:
    headers = organization_headers(organization_id)

    source = postgres_client.post(
        "/api/v1/knowledge-objects",
        headers=headers,
        json={
            "type": "instruction",
            "metadata": {"name": "Source", "approved": True, "score": 1},
        },
    ).json()
    target = postgres_client.post(
        "/api/v1/knowledge-objects",
        headers=headers,
        json={
            "type": "risk",
            "metadata": {"name": "Target", "approved": True, "score": 1},
        },
    ).json()

    for object_id in (source["id"], target["id"]):
        postgres_client.post(
            f"/api/v1/knowledge-objects/{object_id}/archive",
            headers=headers,
        )
        postgres_client.post(
            f"/api/v1/knowledge-objects/{object_id}/restore",
            headers=headers,
        )

    relation = postgres_client.post(
        "/api/v1/relations",
        headers=headers,
        json={
            "source_object_id": source["id"],
            "target_object_id": target["id"],
            "type": "references",
        },
    )
    assert relation.status_code == 201
    relation_body = relation.json()

    outgoing = postgres_client.get(
        f"/api/v1/knowledge-objects/{source['id']}/relations/outgoing",
        headers=headers,
    )
    assert outgoing.status_code == 200
    assert len(outgoing.json()["items"]) == 1

    incoming = postgres_client.get(
        f"/api/v1/knowledge-objects/{target['id']}/relations/incoming",
        headers=headers,
    )
    assert incoming.status_code == 200
    assert len(incoming.json()["items"]) == 1

    connected = postgres_client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected",
        headers=headers,
        params={"direction": "outgoing"},
    )
    assert connected.status_code == 200
    assert connected.json()["items"][0]["id"] == target["id"]

    search_response = postgres_client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "type": "instruction",
            "status": "active",
            "metadata": json.dumps({"approved": True, "score": 1}),
            "limit": 10,
            "offset": 0,
        },
    )
    assert search_response.status_code == 200
    search_body = search_response.json()
    assert search_body["pagination"]["total"] == 1
    assert search_body["items"][0]["id"] == source["id"]

    typed_miss = postgres_client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={"metadata": json.dumps({"approved": 1})},
    )
    assert typed_miss.json()["pagination"]["total"] == 0

    include_deleted = postgres_client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={"include_deleted": "true", "type": "instruction"},
    )
    assert include_deleted.status_code == 200

    delete_relation = postgres_client.delete(
        f"/api/v1/relations/{relation_body['id']}",
        headers=headers,
    )
    assert delete_relation.status_code == 204

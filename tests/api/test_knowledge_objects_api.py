from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.error_codes import (
    KNOWLEDGE_OBJECT_ALREADY_ARCHIVED,
    KNOWLEDGE_OBJECT_ALREADY_ACTIVE,
    KNOWLEDGE_OBJECT_ALREADY_DELETED,
    KNOWLEDGE_OBJECT_NOT_FOUND,
    KNOWLEDGE_OBJECT_VERSION_CONFLICT,
    REQUEST_VALIDATION_ERROR,
)
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import REQUEST_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.infrastructure.persistence.in_memory import InMemoryKnowledgeObjectRepository
from tests.api.knowledge_objects_helpers import (
    create_object,
    organization_headers,
)


def test_create_returns_201_with_location_and_request_id(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={
            "type": "policy",
            "metadata": {"title": "Information Security Policy"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["organization_id"] == str(organization_id)
    assert body["type"] == "policy"
    assert body["status"] == "draft"
    assert body["version"] == 1
    assert body["metadata"] == {"title": "Information Security Policy"}
    assert "created_at" in body
    assert "updated_at" in body
    assert response.headers["Location"] == f"/api/v1/knowledge-objects/{body['id']}"
    assert REQUEST_ID_HEADER in response.headers


def test_create_preserves_metadata_json_types(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    metadata = {
        "enabled": True,
        "count": 3,
        "label": "alpha",
        "nested": {"values": [1, False, None]},
    }

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={"type": "policy", "metadata": metadata},
    )

    assert response.status_code == 201
    assert response.json()["metadata"] == metadata


def test_create_rejects_invalid_organization_id(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge-objects",
        headers={ORGANIZATION_ID_HEADER: "not-a-uuid"},
        json={"type": "policy", "metadata": {"title": "Policy"}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_create_rejects_invalid_type(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={"type": "   ", "metadata": {"title": "Policy"}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_create_rejects_non_object_metadata(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    scalar_response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={"type": "policy", "metadata": "not-an-object"},
    )
    array_response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={"type": "policy", "metadata": []},
    )

    assert scalar_response.status_code == 422
    assert array_response.status_code == 422
    assert scalar_response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_get_existing_object(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
    )

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_object_returns_404(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = client.get(
        f"/api/v1/knowledge-objects/{uuid4()}",
        headers=organization_headers(organization_id),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND
    assert REQUEST_ID_HEADER in response.headers


def test_get_invalid_path_id_returns_422(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = client.get(
        "/api/v1/knowledge-objects/not-a-uuid",
        headers=organization_headers(organization_id),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_get_cross_organization_returns_not_found(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)
    other_organization_id = uuid4()

    response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(other_organization_id),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND


def test_update_increments_version_and_preserves_history(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.put(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
        json={
            "version": 1,
            "metadata": {"title": "Updated Information Security Policy"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    assert body["metadata"] == {"title": "Updated Information Security Policy"}

    history_response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}/history",
        headers=organization_headers(organization_id),
    )
    assert history_response.status_code == 200
    history = history_response.json()["items"]
    assert len(history) == 1
    assert history[0]["version"] == 1
    assert history[0]["metadata"] == {"title": "Information Security Policy"}


def test_update_stale_version_returns_409(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    stale_response = client.put(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
        json={"version": 2, "metadata": {"title": "Stale"}},
    )

    assert stale_response.status_code == 409
    assert stale_response.json()["error"]["code"] == KNOWLEDGE_OBJECT_VERSION_CONFLICT


def test_update_cross_organization_is_blocked(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.put(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(uuid4()),
        json={"version": 1, "metadata": {"title": "Blocked"}},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND


def test_archive_restore_and_delete_lifecycle(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    archive_response = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/archive",
        headers=organization_headers(organization_id),
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    already_archived = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/archive",
        headers=organization_headers(organization_id),
    )
    assert already_archived.status_code == 409
    assert already_archived.json()["error"]["code"] == KNOWLEDGE_OBJECT_ALREADY_ARCHIVED

    restore_response = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/restore",
        headers=organization_headers(organization_id),
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "active"

    already_active = client.post(
        f"/api/v1/knowledge-objects/{created['id']}/restore",
        headers=organization_headers(organization_id),
    )
    assert already_active.status_code == 409
    assert already_active.json()["error"]["code"] == KNOWLEDGE_OBJECT_ALREADY_ACTIVE

    delete_response = client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
    )
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    repeated_delete = client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
    )
    assert repeated_delete.status_code == 409
    assert repeated_delete.json()["error"]["code"] == KNOWLEDGE_OBJECT_ALREADY_DELETED


def test_deleted_object_cannot_be_updated_or_archived_or_restored(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)
    object_id = created["id"]

    client.delete(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=organization_headers(organization_id),
    )

    update_response = client.put(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=organization_headers(organization_id),
        json={"version": 2, "metadata": {"title": "Blocked"}},
    )
    archive_response = client.post(
        f"/api/v1/knowledge-objects/{object_id}/archive",
        headers=organization_headers(organization_id),
    )
    restore_response = client.post(
        f"/api/v1/knowledge-objects/{object_id}/restore",
        headers=organization_headers(organization_id),
    )

    assert update_response.status_code == 409
    assert archive_response.status_code == 409
    assert restore_response.status_code == 409


def test_history_for_version_one_is_empty(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.get(
        f"/api/v1/knowledge-objects/{created['id']}/history",
        headers=organization_headers(organization_id),
    )

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_history_returns_previous_versions_in_order(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)
    object_id = created["id"]

    client.put(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=organization_headers(organization_id),
        json={"version": 1, "metadata": {"title": "Version 2"}},
    )
    client.post(
        f"/api/v1/knowledge-objects/{object_id}/archive",
        headers=organization_headers(organization_id),
    )

    response = client.get(
        f"/api/v1/knowledge-objects/{object_id}/history",
        headers=organization_headers(organization_id),
    )

    history = response.json()["items"]
    assert [item["version"] for item in history] == [1, 2]
    assert history[0]["status"] == "draft"
    assert history[1]["status"] == "draft"


def test_command_commits_and_query_does_not_commit(
    app: FastAPI,
    app_settings: AppSettings,
) -> None:
    from backend.api.dependencies import get_readiness_check, get_settings, get_uow_factory
    from backend.core.infrastructure.persistence.in_memory import (
        InMemoryKnowledgeObjectRelationRepository,
        InMemoryUnitOfWork,
    )

    class CommitTrackingUnitOfWork(InMemoryUnitOfWork):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.commit_calls = 0

        def commit(self) -> None:
            self.commit_calls += 1
            super().commit()

    knowledge_objects = InMemoryKnowledgeObjectRepository()
    relations = InMemoryKnowledgeObjectRelationRepository()
    instances: list[CommitTrackingUnitOfWork] = []

    def uow_factory() -> CommitTrackingUnitOfWork:
        uow = CommitTrackingUnitOfWork(
            knowledge_objects=knowledge_objects,
            relations=relations,
        )
        instances.append(uow)
        return uow

    app.dependency_overrides[get_settings] = lambda: app_settings
    app.dependency_overrides[get_readiness_check] = lambda: (lambda: None)
    app.dependency_overrides[get_uow_factory] = lambda: uow_factory

    organization_id = uuid4()
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/knowledge-objects",
            headers=organization_headers(organization_id),
            json={"type": "policy", "metadata": {"title": "Policy"}},
        )
        assert create_response.status_code == 201
        assert instances[0].commit_calls == 1

        object_id = create_response.json()["id"]
        get_response = client.get(
            f"/api/v1/knowledge-objects/{object_id}",
            headers=organization_headers(organization_id),
        )
        assert get_response.status_code == 200
        assert instances[1].commit_calls == 0

    app.dependency_overrides.clear()

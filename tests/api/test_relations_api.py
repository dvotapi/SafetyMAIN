from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.error_codes import (
    DUPLICATE_KNOWLEDGE_OBJECT_RELATION,
    KNOWLEDGE_OBJECT_NOT_FOUND,
    KNOWLEDGE_OBJECT_RELATION_NOT_FOUND,
    REQUEST_VALIDATION_ERROR,
    SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION,
)
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import REQUEST_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryUnitOfWork,
)
from tests.api.knowledge_objects_helpers import organization_headers
from tests.api.relations_helpers import create_relation, create_source_and_target


def test_create_relation_returns_201_with_location(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)

    response = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json={
            "source_object_id": source["id"],
            "target_object_id": target["id"],
            "type": "references",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["organization_id"] == str(organization_id)
    assert body["source_object_id"] == source["id"]
    assert body["target_object_id"] == target["id"]
    assert body["type"] == "references"
    assert response.headers["Location"] == f"/api/v1/relations/{body['id']}"
    assert REQUEST_ID_HEADER in response.headers


def test_reverse_relation_is_allowed(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)

    first = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
        relation_type="uses",
    )
    second = create_relation(
        client,
        organization_id,
        source_object_id=target["id"],
        target_object_id=source["id"],
        relation_type="uses",
    )

    assert first["id"] != second["id"]


def test_duplicate_relation_returns_409(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    payload = {
        "source_object_id": source["id"],
        "target_object_id": target["id"],
        "type": "references",
    }

    assert client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json=payload,
    ).status_code == 201

    duplicate = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json=payload,
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == DUPLICATE_KNOWLEDGE_OBJECT_RELATION


def test_self_reference_returns_422(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, _target = create_source_and_target(client, organization_id)

    response = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json={
            "source_object_id": source["id"],
            "target_object_id": source["id"],
            "type": "references",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION


def test_create_with_missing_source_returns_404(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    _source, target = create_source_and_target(client, organization_id)

    response = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json={
            "source_object_id": str(uuid4()),
            "target_object_id": target["id"],
            "type": "references",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND


def test_create_with_cross_organization_source_returns_404(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    other_organization_id = uuid4()
    foreign_source = create_source_and_target(client, other_organization_id)[0]
    target = create_source_and_target(client, organization_id)[1]

    response = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json={
            "source_object_id": foreign_source["id"],
            "target_object_id": target["id"],
            "type": "references",
        },
    )

    assert response.status_code == 404


def test_get_and_delete_relation(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    created = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
    )

    get_response = client.get(
        f"/api/v1/relations/{created['id']}",
        headers=organization_headers(organization_id),
    )
    assert get_response.status_code == 200
    assert get_response.json() == created

    delete_response = client.delete(
        f"/api/v1/relations/{created['id']}",
        headers=organization_headers(organization_id),
    )
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    missing = client.get(
        f"/api/v1/relations/{created['id']}",
        headers=organization_headers(organization_id),
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == KNOWLEDGE_OBJECT_RELATION_NOT_FOUND


def test_get_relation_cross_organization_returns_404(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    created = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
    )

    response = client.get(
        f"/api/v1/relations/{created['id']}",
        headers=organization_headers(uuid4()),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == KNOWLEDGE_OBJECT_RELATION_NOT_FOUND


def test_outgoing_and_incoming_traversal(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    relation = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
        relation_type="uses",
    )

    outgoing = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/relations/outgoing",
        headers=organization_headers(organization_id),
    )
    incoming = client.get(
        f"/api/v1/knowledge-objects/{target['id']}/relations/incoming",
        headers=organization_headers(organization_id),
    )

    assert outgoing.status_code == 200
    assert outgoing.json()["items"] == [relation]
    assert incoming.status_code == 200
    assert incoming.json()["items"] == [relation]

    empty = client.get(
        f"/api/v1/knowledge-objects/{target['id']}/relations/outgoing",
        headers=organization_headers(organization_id),
    )
    assert empty.json()["items"] == []


def test_connected_objects_support_direction_and_filtering(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
        relation_type="uses",
    )

    default_response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected",
        headers=organization_headers(organization_id),
    )
    both_response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected?direction=both",
        headers=organization_headers(organization_id),
    )
    incoming_response = client.get(
        f"/api/v1/knowledge-objects/{target['id']}/connected?direction=incoming",
        headers=organization_headers(organization_id),
    )
    filtered_response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected?direction=outgoing&type=uses",
        headers=organization_headers(organization_id),
    )

    assert default_response.status_code == 200
    assert len(default_response.json()["items"]) == 1
    assert default_response.json()["items"][0]["id"] == target["id"]
    assert both_response.json()["items"][0]["id"] == target["id"]
    assert incoming_response.json()["items"][0]["id"] == source["id"]
    assert filtered_response.json()["items"][0]["id"] == target["id"]
    assert "metadata" in filtered_response.json()["items"][0]


def test_invalid_direction_returns_422(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, _target = create_source_and_target(client, organization_id)

    response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected?direction=recursive",
        headers=organization_headers(organization_id),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_relation_commands_commit_and_queries_do_not(
    app: FastAPI,
    app_settings: AppSettings,
) -> None:
    from backend.api.dependencies import get_readiness_check, get_settings, get_uow_factory

    class CommitTrackingUnitOfWork(InMemoryUnitOfWork):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.commit_calls = 0

        def commit(self) -> None:
            self.commit_calls += 1
            super().commit()

    knowledge_objects = __import__(
        "backend.core.infrastructure.persistence.in_memory",
        fromlist=["InMemoryKnowledgeObjectRepository"],
    ).InMemoryKnowledgeObjectRepository()
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
        source, target = create_source_and_target(client, organization_id)
        create_response = client.post(
            "/api/v1/relations",
            headers=organization_headers(organization_id),
            json={
                "source_object_id": source["id"],
                "target_object_id": target["id"],
                "type": "references",
            },
        )
        assert create_response.status_code == 201
        assert instances[2].commit_calls == 1

        relation_id = create_response.json()["id"]
        list_response = client.get(
            f"/api/v1/knowledge-objects/{source['id']}/relations/outgoing",
            headers=organization_headers(organization_id),
        )
        assert list_response.status_code == 200
        assert instances[3].commit_calls == 0

        delete_response = client.delete(
            f"/api/v1/relations/{relation_id}",
            headers=organization_headers(organization_id),
        )
        assert delete_response.status_code == 204
        assert instances[4].commit_calls == 1

    app.dependency_overrides.clear()


def test_invalid_organization_header_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/relations",
        headers={ORGANIZATION_ID_HEADER: "invalid"},
        json={
            "source_object_id": str(uuid4()),
            "target_object_id": str(uuid4()),
            "type": "references",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR

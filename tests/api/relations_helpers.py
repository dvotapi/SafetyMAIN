from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from tests.api.knowledge_objects_helpers import create_object, organization_headers


def create_source_and_target(
    client: TestClient,
    organization_id: UUID,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    source = create_object(
        client,
        organization_id,
        object_type="instruction",
        metadata={"name": "Source"},
        headers=headers,
    )
    target = create_object(
        client,
        organization_id,
        object_type="risk",
        metadata={"name": "Target"},
        headers=headers,
    )
    return source, target


def create_relation(
    client: TestClient,
    organization_id: UUID,
    *,
    source_object_id: UUID | str,
    target_object_id: UUID | str,
    relation_type: str = "references",
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/relations",
        headers=headers or organization_headers(organization_id),
        json={
            "source_object_id": str(source_object_id),
            "target_object_id": str(target_object_id),
            "type": relation_type,
        },
    )
    assert response.status_code == 201
    return response.json()

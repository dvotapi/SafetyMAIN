from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api.error_codes import KNOWLEDGE_OBJECT_NOT_FOUND
from backend.api.middleware import REQUEST_ID_HEADER
from tests.api.contracts.assertions import assert_request_id_header
from tests.api.knowledge_objects_helpers import organization_headers


def test_knowledge_object_http_lifecycle(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    headers = organization_headers(organization_id)
    metadata = {
        "title": "Lifecycle Policy",
        "enabled": True,
        "count": 3,
        "nested": {"values": [1, False, None]},
    }

    create_response = client.post(
        "/api/v1/knowledge-objects",
        headers=headers,
        json={"type": "policy", "metadata": metadata},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert_request_id_header(create_response)
    assert created["status"] == "draft"
    assert created["version"] == 1
    assert created["metadata"] == metadata
    object_id = created["id"]

    get_response = client.get(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json() == created

    updated_metadata = {
        **metadata,
        "title": "Updated Lifecycle Policy",
        "revision": 2,
    }
    update_response = client.put(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
        json={"version": 1, "metadata": updated_metadata},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["version"] == 2
    assert updated["metadata"] == updated_metadata

    history_response = client.get(
        f"/api/v1/knowledge-objects/{object_id}/history",
        headers=headers,
    )
    assert history_response.status_code == 200
    history_items = history_response.json()["items"]
    assert len(history_items) == 1
    assert history_items[0]["version"] == 1
    assert history_items[0]["metadata"] == metadata

    archive_response = client.post(
        f"/api/v1/knowledge-objects/{object_id}/archive",
        headers=headers,
    )
    assert archive_response.status_code == 200
    archived = archive_response.json()
    assert archived["status"] == "archived"
    assert archived["version"] == updated["version"] + 1

    restore_response = client.post(
        f"/api/v1/knowledge-objects/{object_id}/restore",
        headers=headers,
    )
    assert restore_response.status_code == 200
    restored = restore_response.json()
    assert restored["status"] == "active"
    assert restored["version"] == archived["version"] + 1

    delete_response = client.delete(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
    )
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert REQUEST_ID_HEADER in delete_response.headers

    cross_org_response = client.get(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=organization_headers(uuid4()),
    )
    assert cross_org_response.status_code == 404
    assert cross_org_response.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND

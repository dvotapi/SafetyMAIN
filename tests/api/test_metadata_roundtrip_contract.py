from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.api.knowledge_objects_helpers import organization_headers


def test_metadata_types_survive_http_round_trip(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    headers = organization_headers(organization_id)
    metadata = {
        "enabled": True,
        "count": 3,
        "label": "alpha",
        "ratio": 1.5,
        "missing": None,
        "nested": {"values": [1, False, None]},
    }

    create_response = client.post(
        "/api/v1/knowledge-objects",
        headers=headers,
        json={"type": "policy", "metadata": metadata},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    object_id = created["id"]

    get_response = client.get(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
    )
    assert get_response.json()["metadata"] == metadata

    updated_metadata = {
        **metadata,
        "count": 4,
        "nested": {"values": [2, True, "beta"]},
    }
    update_response = client.put(
        f"/api/v1/knowledge-objects/{object_id}",
        headers=headers,
        json={"version": 1, "metadata": updated_metadata},
    )
    assert update_response.json()["metadata"] == updated_metadata

    history_response = client.get(
        f"/api/v1/knowledge-objects/{object_id}/history",
        headers=headers,
    )
    assert history_response.json()["items"][0]["metadata"] == metadata

    search_response = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "metadata": json.dumps({"enabled": True, "count": 4}),
        },
    )
    assert search_response.status_code == 200
    assert search_response.json()["pagination"]["total"] == 0

    typed_search = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "metadata": json.dumps({"enabled": True}),
        },
    )
    assert typed_search.json()["pagination"]["total"] == 0

    restore_after_archive = client.post(
        f"/api/v1/knowledge-objects/{object_id}/archive",
        headers=headers,
    )
    assert restore_after_archive.status_code == 200
    archived_metadata = restore_after_archive.json()["metadata"]
    assert archived_metadata == updated_metadata

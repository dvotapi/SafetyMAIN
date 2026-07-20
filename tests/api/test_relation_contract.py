from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api.error_codes import (
    DUPLICATE_KNOWLEDGE_OBJECT_RELATION,
    KNOWLEDGE_OBJECT_RELATION_NOT_FOUND,
    SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION,
)
from tests.api.knowledge_objects_helpers import organization_headers
from tests.api.relations_helpers import create_relation, create_source_and_target


def test_relation_http_contract_scenario(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    headers = organization_headers(organization_id)
    source, target = create_source_and_target(client, organization_id)

    create_response = client.post(
        "/api/v1/relations",
        headers=headers,
        json={
            "source_object_id": str(source["id"]),
            "target_object_id": str(target["id"]),
            "type": "references",
        },
    )
    assert create_response.status_code == 201
    relation = create_response.json()

    get_response = client.get(
        f"/api/v1/relations/{relation['id']}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json() == relation

    outgoing_response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/relations/outgoing",
        headers=headers,
    )
    assert outgoing_response.status_code == 200
    assert len(outgoing_response.json()["items"]) == 1
    assert outgoing_response.json()["items"][0]["id"] == relation["id"]

    incoming_response = client.get(
        f"/api/v1/knowledge-objects/{target['id']}/relations/incoming",
        headers=headers,
    )
    assert incoming_response.status_code == 200
    assert len(incoming_response.json()["items"]) == 1

    connected_response = client.get(
        f"/api/v1/knowledge-objects/{source['id']}/connected",
        headers=headers,
        params={"direction": "outgoing"},
    )
    assert connected_response.status_code == 200
    assert len(connected_response.json()["items"]) == 1
    assert connected_response.json()["items"][0]["id"] == target["id"]

    reverse_relation = create_relation(
        client,
        organization_id,
        source_object_id=target["id"],
        target_object_id=source["id"],
    )
    assert reverse_relation["id"] != relation["id"]

    duplicate_response = client.post(
        "/api/v1/relations",
        headers=headers,
        json={
            "source_object_id": str(source["id"]),
            "target_object_id": str(target["id"]),
            "type": "references",
        },
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == DUPLICATE_KNOWLEDGE_OBJECT_RELATION

    self_reference_response = client.post(
        "/api/v1/relations",
        headers=headers,
        json={
            "source_object_id": str(source["id"]),
            "target_object_id": str(source["id"]),
            "type": "references",
        },
    )
    assert self_reference_response.status_code == 422
    assert (
        self_reference_response.json()["error"]["code"]
        == SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION
    )

    delete_response = client.delete(
        f"/api/v1/relations/{relation['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    missing_response = client.get(
        f"/api/v1/relations/{relation['id']}",
        headers=headers,
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == KNOWLEDGE_OBJECT_RELATION_NOT_FOUND

    source_after_delete = client.get(
        f"/api/v1/knowledge-objects/{source['id']}",
        headers=headers,
    )
    target_after_delete = client.get(
        f"/api/v1/knowledge-objects/{target['id']}",
        headers=headers,
    )
    assert source_after_delete.status_code == 200
    assert target_after_delete.status_code == 200

    cross_org_response = client.get(
        f"/api/v1/relations/{reverse_relation['id']}",
        headers=organization_headers(uuid4()),
    )
    assert cross_org_response.status_code == 404

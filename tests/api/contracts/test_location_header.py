from __future__ import annotations

from fastapi.testclient import TestClient

from tests.api.contracts.assertions import assert_location_header
from tests.api.knowledge_objects_helpers import organization_headers
from tests.api.relations_helpers import create_source_and_target


def test_create_knowledge_object_location_header(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = client.post(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        json={"type": "policy", "metadata": {"title": "Policy"}},
    )

    body = response.json()
    assert_location_header(
        response,
        expected_location=f"/api/v1/knowledge-objects/{body['id']}",
    )


def test_create_relation_location_header(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)

    response = client.post(
        "/api/v1/relations",
        headers=organization_headers(organization_id),
        json={
            "source_object_id": str(source["id"]),
            "target_object_id": str(target["id"]),
            "type": "references",
        },
    )

    body = response.json()
    assert_location_header(
        response,
        expected_location=f"/api/v1/relations/{body['id']}",
    )

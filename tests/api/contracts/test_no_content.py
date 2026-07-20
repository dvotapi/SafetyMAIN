from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.contracts.assertions import assert_no_content_response
from tests.api.knowledge_objects_helpers import create_object, organization_headers
from tests.api.relations_helpers import create_relation, create_source_and_target


def test_delete_knowledge_object_returns_empty_body(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(organization_id),
    )

    assert_no_content_response(response)


def test_delete_relation_returns_empty_body(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    source, target = create_source_and_target(client, organization_id)
    relation = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
    )

    response = client.delete(
        f"/api/v1/relations/{relation['id']}",
        headers=organization_headers(organization_id),
    )

    assert_no_content_response(response)


def test_delete_knowledge_object_cross_organization_is_not_found(
    knowledge_object_client: tuple[TestClient, object, object],
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)

    response = client.delete(
        f"/api/v1/knowledge-objects/{created['id']}",
        headers=organization_headers(uuid4()),
    )

    assert response.status_code == 404

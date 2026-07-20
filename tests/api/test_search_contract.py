from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.infrastructure.persistence.in_memory import InMemoryKnowledgeObjectRepository
from tests.api.knowledge_objects_helpers import organization_headers, seed_knowledge_object


def test_search_http_contract_scenario(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    other_organization_id = uuid4()
    headers = organization_headers(organization_id)

    matching = seed_knowledge_object(
        repository,
        organization_id,
        object_type="policy",
        status=KnowledgeObjectStatus.ACTIVE,
        metadata={"department": "security", "approved": True, "score": 1},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        object_type="policy",
        status=KnowledgeObjectStatus.ARCHIVED,
        metadata={"department": "security", "approved": True, "score": 1},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        object_type="policy",
        status=KnowledgeObjectStatus.DELETED,
        metadata={"department": "security", "approved": True, "score": 1},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        object_type="risk",
        status=KnowledgeObjectStatus.ACTIVE,
        metadata={"department": "security", "approved": True, "score": 1},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        object_type="policy",
        status=KnowledgeObjectStatus.ACTIVE,
        metadata={"department": "security", "approved": True, "score": "1"},
    )
    seed_knowledge_object(
        repository,
        other_organization_id,
        object_type="policy",
        status=KnowledgeObjectStatus.ACTIVE,
        metadata={"department": "security", "approved": True, "score": 1},
    )
    for index in range(3):
        seed_knowledge_object(
            repository,
            organization_id,
            object_type="policy",
            status=KnowledgeObjectStatus.ACTIVE,
            metadata={"department": "security", "approved": True, "score": 1, "page": index},
        )

    filtered_response = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "type": "policy",
            "status": "active",
            "metadata": json.dumps(
                {"department": "security", "approved": True, "score": 1}
            ),
            "limit": 2,
            "offset": 0,
        },
    )
    assert filtered_response.status_code == 200
    filtered_body = filtered_response.json()
    assert filtered_body["pagination"]["total"] == 4
    assert len(filtered_body["items"]) == 2
    assert all(item["type"] == "policy" for item in filtered_body["items"])
    assert all(item["status"] == "active" for item in filtered_body["items"])
    assert filtered_body["items"][0]["id"] == str(matching.header.id.value)

    second_page = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "type": "policy",
            "status": "active",
            "metadata": json.dumps(
                {"department": "security", "approved": True, "score": 1}
            ),
            "limit": 2,
            "offset": 2,
        },
    )
    assert second_page.status_code == 200
    assert second_page.json()["pagination"]["total"] == 4
    assert len(second_page.json()["items"]) == 2

    deleted_only = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={"status": "deleted"},
    )
    assert deleted_only.status_code == 200
    assert deleted_only.json()["pagination"]["total"] == 1

    include_deleted = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={"include_deleted": "true", "type": "policy"},
    )
    assert include_deleted.status_code == 200
    assert include_deleted.json()["pagination"]["total"] == 7

    other_org_results = client.get(
        "/api/v1/knowledge-objects",
        headers=organization_headers(other_organization_id),
    )
    assert other_org_results.status_code == 200
    assert other_org_results.json()["pagination"]["total"] == 1

    repeated = client.get(
        "/api/v1/knowledge-objects",
        headers=headers,
        params={
            "type": "policy",
            "status": "active",
            "metadata": json.dumps(
                {"department": "security", "approved": True, "score": 1}
            ),
            "limit": 2,
            "offset": 0,
        },
    )
    assert repeated.json()["items"] == filtered_body["items"]

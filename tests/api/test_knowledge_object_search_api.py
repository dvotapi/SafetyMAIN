from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import get_uow_factory
from backend.api.error_codes import REQUEST_VALIDATION_ERROR
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.mappers.knowledge_objects import to_knowledge_object_responses
from backend.api.middleware import REQUEST_ID_HEADER
from backend.core.application.handlers.search_knowledge_objects import (
    SearchKnowledgeObjectsHandler,
)
from backend.core.application.queries.search_knowledge_objects import (
    SearchKnowledgeObjectsQuery,
)
from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.value_objects import OrganizationId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)
from tests.api.knowledge_objects_helpers import (
    organization_headers,
    seed_knowledge_object,
)


def search(
    client: TestClient,
    organization_id: UUID,
    **params: object,
) -> object:
    return client.get(
        "/api/v1/knowledge-objects",
        headers=organization_headers(organization_id),
        params=params,
    )


def test_empty_search_returns_200_with_defaults(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    active = seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.DRAFT)
    seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.DELETED)

    response = search(client, organization_id)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(active.header.id.value)
    assert body["items"][0]["status"] == "active"
    assert body["pagination"] == {"offset": 0, "limit": 50, "total": 1}
    assert REQUEST_ID_HEADER in response.headers


def test_search_requires_organization_header(client: TestClient) -> None:
    response = client.get("/api/v1/knowledge-objects")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_search_rejects_invalid_organization_id(client: TestClient) -> None:
    response = client.get(
        "/api/v1/knowledge-objects",
        headers={ORGANIZATION_ID_HEADER: "not-a-uuid"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_search_excludes_other_organizations(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    expected = seed_knowledge_object(repository, organization_id)
    seed_knowledge_object(repository, uuid4())

    response = search(client, organization_id)

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["id"] == str(expected.header.id.value)


def test_search_filters_by_type(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    policy = seed_knowledge_object(
        repository,
        organization_id,
        object_type="policy",
        metadata={"department": "security"},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        object_type="risk",
        metadata={"department": "security"},
    )

    response = search(
        client,
        organization_id,
        type="policy",
        metadata=json.dumps({"department": "security"}),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(policy.header.id.value)
    assert body["pagination"]["total"] == 1


def test_search_rejects_empty_type(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = search(client, organization_id, type="   ")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


@pytest.mark.parametrize(
    ("status", "expected_status"),
    [
        ("active", "active"),
        ("archived", "archived"),
        ("deleted", "deleted"),
    ],
)
def test_search_filters_by_status(
    status: str,
    expected_status: str,
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    expected = seed_knowledge_object(
        repository,
        organization_id,
        status=KnowledgeObjectStatus[expected_status.upper()],
    )
    if expected_status != "active":
        seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    if expected_status != "archived":
        seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.ARCHIVED)
    if expected_status != "deleted":
        seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.DELETED)

    response = search(client, organization_id, status=status)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(expected.header.id.value)
    assert body["items"][0]["status"] == expected_status


def test_search_rejects_invalid_status(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = search(client, organization_id, status="pending")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


@pytest.mark.parametrize(
    ("include_deleted", "expected_count"),
    [
        (None, 1),
        ("false", 1),
        ("true", 2),
    ],
)
def test_include_deleted_behavior(
    include_deleted: str | None,
    expected_count: int,
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    seed_knowledge_object(repository, organization_id, status=KnowledgeObjectStatus.DELETED)

    params: dict[str, object] = {}
    if include_deleted is not None:
        params["include_deleted"] = include_deleted

    response = search(client, organization_id, **params)

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == expected_count


def test_status_deleted_without_include_deleted(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    deleted = seed_knowledge_object(
        repository,
        organization_id,
        status=KnowledgeObjectStatus.DELETED,
    )

    response = search(client, organization_id, status="deleted")

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    assert response.json()["items"][0]["id"] == str(deleted.header.id.value)


def test_status_deleted_with_include_deleted_false_is_rejected(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = search(client, organization_id, status="deleted", include_deleted="false")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_metadata_filter_and_semantics(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    expected = seed_knowledge_object(
        repository,
        organization_id,
        metadata={"department": "security", "approved": True, "revision": 3},
    )
    seed_knowledge_object(
        repository,
        organization_id,
        metadata={"department": "security", "approved": False, "revision": 3},
    )

    response = search(
        client,
        organization_id,
        metadata=json.dumps({"department": "security", "approved": True, "revision": 3}),
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    assert response.json()["items"][0]["id"] == str(expected.header.id.value)


def test_metadata_type_sensitive_matching(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id, metadata={"approved": True})

    response = search(
        client,
        organization_id,
        metadata=json.dumps({"approved": 1}),
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    ("metadata", "expected_status"),
    [
        ('{"department":"security","department":"legal"}', 422),
        ("[]", 422),
        ('"scalar"', 422),
        ("{not-json", 422),
        ("{}", 200),
    ],
)
def test_metadata_validation(
    metadata: str,
    expected_status: int,
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = search(client, organization_id, metadata=metadata)

    assert response.status_code == expected_status
    if expected_status == 422:
        assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_pagination_defaults_and_second_page(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    objects = [
        seed_knowledge_object(
            repository,
            organization_id,
            metadata={"index": index},
        )
        for index in range(3)
    ]

    first_page = search(client, organization_id, limit=2, offset=0)
    second_page = search(client, organization_id, limit=2, offset=2)

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["pagination"] == {"offset": 0, "limit": 2, "total": 3}
    assert second_page.json()["pagination"] == {"offset": 2, "limit": 2, "total": 3}
    assert len(first_page.json()["items"]) == 2
    assert len(second_page.json()["items"]) == 1
    assert first_page.json()["items"][0]["id"] == str(objects[0].header.id.value)
    assert second_page.json()["items"][0]["id"] == str(objects[2].header.id.value)


def test_offset_beyond_total_returns_empty_items(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id)

    response = search(client, organization_id, offset=99)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["pagination"]["total"] == 1


@pytest.mark.parametrize(
    ("params",),
    [
        ({"offset": -1},),
        ({"limit": 0},),
        ({"limit": 101},),
        ({"include_deleted": "maybe"},),
    ],
)
def test_search_rejects_invalid_pagination_and_boolean(
    params: dict[str, object],
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, _repository, organization_id = knowledge_object_client

    response = search(client, organization_id, **params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == REQUEST_VALIDATION_ERROR


def test_search_ordering_is_deterministic(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    first = seed_knowledge_object(
        repository,
        organization_id,
        metadata={"label": "first"},
    )
    second = seed_knowledge_object(
        repository,
        organization_id,
        metadata={"label": "second"},
    )

    first_response = search(client, organization_id)
    second_response = search(client, organization_id)

    expected_ids = [str(first.header.id.value), str(second.header.id.value)]
    assert [item["id"] for item in first_response.json()["items"]] == expected_ids
    assert [item["id"] for item in second_response.json()["items"]] == expected_ids


def test_collection_and_detail_routes_both_resolve(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    knowledge_object = seed_knowledge_object(repository, organization_id)

    collection_response = search(client, organization_id)
    detail_response = client.get(
        f"/api/v1/knowledge-objects/{knowledge_object.header.id.value}",
        headers=organization_headers(organization_id),
    )

    assert collection_response.status_code == 200
    assert detail_response.status_code == 200
    assert collection_response.json()["items"][0]["id"] == detail_response.json()["id"]


def test_search_reuses_knowledge_object_mapper(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    knowledge_object = seed_knowledge_object(repository, organization_id)

    response = search(client, organization_id)
    mapped = to_knowledge_object_responses((knowledge_object,))

    assert response.status_code == 200
    assert response.json()["items"][0] == mapped[0].model_dump(mode="json")


def test_search_does_not_commit(
    app: FastAPI,
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id)
    inner_factory = app.dependency_overrides[get_uow_factory]()
    commit_calls = 0

    def counting_factory() -> InMemoryUnitOfWork:
        unit_of_work = inner_factory()
        original_commit = unit_of_work.commit

        def counted_commit() -> None:
            nonlocal commit_calls
            commit_calls += 1
            original_commit()

        unit_of_work.commit = counted_commit  # type: ignore[method-assign]
        return unit_of_work

    app.dependency_overrides[get_uow_factory] = lambda: counting_factory

    response = search(client, organization_id)

    assert response.status_code == 200
    assert commit_calls == 0


def test_search_handler_does_not_mutate_repository_state(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id)

    first = search(client, organization_id)
    second = search(client, organization_id)

    assert first.json() == second.json()


def test_direct_handler_search_does_not_commit(
    knowledge_object_client: tuple[TestClient, InMemoryKnowledgeObjectRepository, UUID],
) -> None:
    _client, repository, organization_id = knowledge_object_client
    seed_knowledge_object(repository, organization_id)
    unit_of_work = InMemoryUnitOfWork(knowledge_objects=repository)
    unit_of_work.committed = False

    SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=OrganizationId(value=organization_id))
    )

    assert unit_of_work.committed is False

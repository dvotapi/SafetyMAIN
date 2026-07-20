from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api.error_codes import REQUEST_VALIDATION_ERROR
from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from tests.api.contracts.assertions import assert_error_envelope
from tests.api.knowledge_objects_helpers import create_object
from tests.api.relations_helpers import create_relation, create_source_and_target


BUSINESS_ENDPOINTS = [
    ("POST", "/api/v1/knowledge-objects", {"type": "policy", "metadata": {"title": "A"}}),
    ("GET", "/api/v1/knowledge-objects", None),
    ("PUT", "/api/v1/knowledge-objects/{object_id}", {"version": 1, "metadata": {"title": "B"}}),
    ("POST", "/api/v1/knowledge-objects/{object_id}/archive", None),
    ("POST", "/api/v1/knowledge-objects/{object_id}/restore", None),
    ("DELETE", "/api/v1/knowledge-objects/{object_id}", None),
    ("GET", "/api/v1/knowledge-objects/{object_id}/history", None),
    ("POST", "/api/v1/relations", None),
    ("GET", "/api/v1/relations/{relation_id}", None),
    ("DELETE", "/api/v1/relations/{relation_id}", None),
    ("GET", "/api/v1/knowledge-objects/{object_id}/relations/outgoing", None),
    ("GET", "/api/v1/knowledge-objects/{object_id}/relations/incoming", None),
    ("GET", "/api/v1/knowledge-objects/{object_id}/connected", None),
]


@pytest.mark.parametrize(("method", "path_template", "json_body"), BUSINESS_ENDPOINTS)
def test_business_endpoints_require_organization_header(
    knowledge_object_client: tuple[TestClient, object, object],
    method: str,
    path_template: str,
    json_body: dict[str, object] | None,
) -> None:
    client, _repository, organization_id = knowledge_object_client
    created = create_object(client, organization_id)
    source, target = create_source_and_target(client, organization_id)
    relation = create_relation(
        client,
        organization_id,
        source_object_id=source["id"],
        target_object_id=target["id"],
    )

    path = path_template.format(
        object_id=created["id"],
        relation_id=relation["id"],
    )
    response = client.request(method, path, json=json_body)
    assert response.status_code == 422
    assert_error_envelope(response, status_code=422, code=REQUEST_VALIDATION_ERROR)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/ready"),
    ],
)
def test_system_endpoints_do_not_require_organization_header(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)
    assert response.status_code == 200


def test_malformed_organization_header_returns_validation_error(client: TestClient) -> None:
    response = client.get(
        "/api/v1/knowledge-objects",
        headers={ORGANIZATION_ID_HEADER: "not-a-uuid"},
    )
    assert response.status_code == 422
    assert_error_envelope(response, status_code=422, code=REQUEST_VALIDATION_ERROR)

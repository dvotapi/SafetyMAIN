from __future__ import annotations

from backend.api.app import create_app
from backend.bootstrap.settings import AppSettings


def test_openapi_includes_knowledge_object_paths(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    openapi = application.openapi()
    paths = openapi["paths"]

    assert "/api/v1/knowledge-objects" in paths
    assert "post" in paths["/api/v1/knowledge-objects"]
    assert "get" in paths["/api/v1/knowledge-objects"]
    assert "/api/v1/knowledge-objects/{knowledge_object_id}" in paths
    assert "get" in paths["/api/v1/knowledge-objects/{knowledge_object_id}"]
    assert "put" in paths["/api/v1/knowledge-objects/{knowledge_object_id}"]
    assert "delete" in paths["/api/v1/knowledge-objects/{knowledge_object_id}"]
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/archive" in paths
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/restore" in paths
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/history" in paths

    create_operation = paths["/api/v1/knowledge-objects"]["post"]
    assert "X-Organization-ID" in create_operation["parameters"][0]["name"]

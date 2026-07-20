from __future__ import annotations

from backend.api.app import create_app
from backend.bootstrap.settings import AppSettings


def test_openapi_includes_relation_paths(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    assert "/api/v1/relations" in paths
    assert "post" in paths["/api/v1/relations"]
    assert "/api/v1/relations/{relation_id}" in paths
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/relations/outgoing" in paths
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/relations/incoming" in paths
    assert "/api/v1/knowledge-objects/{knowledge_object_id}/connected" in paths

    connected = paths["/api/v1/knowledge-objects/{knowledge_object_id}/connected"]["get"]
    parameter_names = {item["name"] for item in connected["parameters"]}
    assert "direction" in parameter_names
    assert "type" in parameter_names

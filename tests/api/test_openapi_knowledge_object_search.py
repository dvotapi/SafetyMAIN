from __future__ import annotations

from backend.api.app import create_app
from backend.bootstrap.settings import AppSettings


def test_openapi_documents_knowledge_object_search(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    openapi = application.openapi()
    paths = openapi["paths"]

    search_path = paths["/api/v1/knowledge-objects"]["get"]
    parameter_names = {item["name"] for item in search_path["parameters"]}
    assert "X-Organization-ID" in parameter_names
    assert {"type", "status", "metadata", "include_deleted", "offset", "limit"}.issubset(
        parameter_names
    )

    metadata_parameter = next(
        item for item in search_path["parameters"] if item["name"] == "metadata"
    )
    assert "JSON object" in metadata_parameter["description"]

    status_parameter = next(
        item for item in search_path["parameters"] if item["name"] == "status"
    )
    assert "active" in status_parameter["description"]
    assert "archived" in status_parameter["description"]
    assert "deleted" in status_parameter["description"]

    success_response = search_path["responses"]["200"]
    schema_ref = success_response["content"]["application/json"]["schema"]["$ref"]
    schema_name = schema_ref.rsplit("/", maxsplit=1)[-1]
    search_schema = openapi["components"]["schemas"][schema_name]
    assert "items" in search_schema["properties"]
    assert "pagination" in search_schema["properties"]

    pagination_schema = openapi["components"]["schemas"]["PaginationResponse"]
    assert set(pagination_schema["properties"]) == {"offset", "limit", "total"}

    assert "422" in search_path["responses"]

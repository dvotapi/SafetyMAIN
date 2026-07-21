from __future__ import annotations

from backend.api.app import create_app
from backend.api.middleware import REQUEST_ID_HEADER
from backend.api.operation_ids import STABLE_OPERATION_IDS
from backend.bootstrap.settings import AppSettings


EXPECTED_PATHS: dict[str, set[str]] = {
    "/api/v1/health": {"get"},
    "/api/v1/ready": {"get"},
    "/api/v1/auth/login": {"post"},
    "/api/v1/auth/refresh": {"post"},
    "/api/v1/knowledge-objects": {"get", "post"},
    "/api/v1/knowledge-objects/{knowledge_object_id}": {"get", "put", "delete"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/archive": {"post"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/restore": {"post"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/history": {"get"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/relations/outgoing": {"get"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/relations/incoming": {"get"},
    "/api/v1/knowledge-objects/{knowledge_object_id}/connected": {"get"},
    "/api/v1/relations": {"post"},
    "/api/v1/relations/{relation_id}": {"get", "delete"},
    "/api/v1/admin/users": {"get", "post"},
    "/api/v1/admin/users/{user_id}": {"get", "patch"},
    "/api/v1/admin/users/{user_id}/activate": {"post"},
    "/api/v1/admin/users/{user_id}/deactivate": {"post"},
}


def test_openapi_contains_expected_paths(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    for path, methods in EXPECTED_PATHS.items():
        assert path in paths
        assert methods.issubset(set(paths[path]))


def test_openapi_operation_ids_are_stable_and_unique(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    schema = application.openapi()

    operation_ids = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert operation_ids == set(STABLE_OPERATION_IDS)
    assert len(operation_ids) == len(STABLE_OPERATION_IDS)


def test_openapi_documents_no_content_delete_responses(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    for path in (
        "/api/v1/knowledge-objects/{knowledge_object_id}",
        "/api/v1/relations/{relation_id}",
    ):
        delete_operation = paths[path]["delete"]
        response = delete_operation["responses"]["204"]
        assert "content" not in response
        assert REQUEST_ID_HEADER in response["headers"]


def test_openapi_documents_create_location_headers(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    create_ko = paths["/api/v1/knowledge-objects"]["post"]["responses"]["201"]
    create_relation = paths["/api/v1/relations"]["post"]["responses"]["201"]

    assert "Location" in create_ko["headers"]
    assert "Location" in create_relation["headers"]


def test_openapi_business_routes_require_organization_header(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    business_paths = [
        path
        for path in paths
        if path.startswith("/api/v1/knowledge-objects") or path.startswith("/api/v1/relations")
    ]

    for path in business_paths:
        for operation in paths[path].values():
            if not isinstance(operation, dict):
                continue
            parameter_names = {item["name"] for item in operation.get("parameters", [])}
            assert "X-Organization-ID" in parameter_names


def test_openapi_system_routes_do_not_require_organization_header(
    app_settings: AppSettings,
) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    for path in ("/api/v1/health", "/api/v1/ready", "/api/v1/auth/login", "/api/v1/auth/refresh"):
        for operation in paths[path].values():
            parameter_names = {item["name"] for item in operation.get("parameters", [])}
            assert "X-Organization-ID" not in parameter_names


def test_openapi_documents_bearer_auth_security_scheme(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    schema = application.openapi()

    assert schema["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }


def test_openapi_business_routes_require_bearer_auth(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    business_paths = [
        path
        for path in paths
        if path.startswith("/api/v1/knowledge-objects")
        or path.startswith("/api/v1/relations")
        or path.startswith("/api/v1/admin/users")
    ]

    assert business_paths
    for path in business_paths:
        for operation in paths[path].values():
            if not isinstance(operation, dict):
                continue
            assert operation.get("security") == [{"BearerAuth": []}]


def test_openapi_auth_routes_do_not_require_bearer_auth(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    for path in ("/api/v1/health", "/api/v1/ready", "/api/v1/auth/login", "/api/v1/auth/refresh"):
        for operation in paths[path].values():
            if not isinstance(operation, dict):
                continue
            assert operation.get("security") != [{"BearerAuth": []}]


def test_openapi_protected_routes_document_auth_error_responses(
    app_settings: AppSettings,
) -> None:
    application = create_app(settings=app_settings)
    paths = application.openapi()["paths"]

    create_operation = paths["/api/v1/knowledge-objects"]["post"]
    assert "401" in create_operation["responses"]
    assert "403" in create_operation["responses"]
    unauthorized_schema = create_operation["responses"]["401"]["content"]["application/json"]["schema"]
    assert "$ref" in unauthorized_schema or "properties" in unauthorized_schema

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.error_codes import (
    DUPLICATE_KNOWLEDGE_OBJECT,
    INTERNAL_SERVER_ERROR,
    KNOWLEDGE_OBJECT_NOT_FOUND,
    SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION,
)
from backend.api.middleware import REQUEST_ID_HEADER
from backend.bootstrap.settings import AppSettings
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObject,
    KnowledgeObjectNotFound,
    SelfReferencingKnowledgeObjectRelation,
)
from backend.core.domain.value_objects import KnowledgeObjectId


def _knowledge_object_id() -> KnowledgeObjectId:
    return KnowledgeObjectId(value=uuid4())


def _build_exception_test_app(settings: AppSettings) -> FastAPI:
    application = create_app(settings=settings)

    @application.get("/_test/not-found")
    def raise_not_found() -> None:
        raise KnowledgeObjectNotFound(_knowledge_object_id())

    @application.get("/_test/duplicate")
    def raise_duplicate() -> None:
        raise DuplicateKnowledgeObject(_knowledge_object_id())

    @application.get("/_test/self-relation")
    def raise_self_relation() -> None:
        raise SelfReferencingKnowledgeObjectRelation(_knowledge_object_id())

    @application.get("/_test/unexpected")
    def raise_unexpected() -> None:
        raise RuntimeError("sensitive internal failure details")

    return application


def test_domain_exception_mappings(app_settings: AppSettings) -> None:
    application = _build_exception_test_app(app_settings)
    with TestClient(application, raise_server_exceptions=False) as client:
        not_found = client.get("/_test/not-found")
        assert not_found.status_code == 404
        assert not_found.json()["error"]["code"] == KNOWLEDGE_OBJECT_NOT_FOUND
        assert REQUEST_ID_HEADER in not_found.headers

        conflict = client.get("/_test/duplicate")
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == DUPLICATE_KNOWLEDGE_OBJECT

        invalid = client.get("/_test/self-relation")
        assert invalid.status_code == 422
        assert (
            invalid.json()["error"]["code"] == SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION
        )


def test_unexpected_error_hides_internal_text(app_settings: AppSettings) -> None:
    application = _build_exception_test_app(app_settings)
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/_test/unexpected")
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == INTERNAL_SERVER_ERROR
        assert body["error"]["message"] == "An unexpected error occurred."
        assert "sensitive internal failure details" not in response.text
        assert "RuntimeError" not in response.text
        assert REQUEST_ID_HEADER in response.headers

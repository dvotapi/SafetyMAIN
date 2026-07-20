from __future__ import annotations


from backend.api.error_codes import (
    DOMAIN_EXCEPTION_ERROR_CODES,
    DOMAIN_EXCEPTION_HTTP_STATUS,
    DOMAIN_EXCEPTION_MESSAGES,
    PUBLIC_ERROR_CODES,
    REQUEST_VALIDATION_ERROR,
    REQUEST_VALIDATION_MESSAGE,
)
from backend.core.domain.exceptions import SafetyMainDomainError


def test_public_error_codes_include_transport_codes() -> None:
    assert REQUEST_VALIDATION_ERROR in PUBLIC_ERROR_CODES
    assert "internal_server_error" in PUBLIC_ERROR_CODES
    assert "service_not_ready" in PUBLIC_ERROR_CODES


def test_domain_exception_registry_is_complete() -> None:
    assert set(DOMAIN_EXCEPTION_HTTP_STATUS) == set(DOMAIN_EXCEPTION_ERROR_CODES)
    assert set(DOMAIN_EXCEPTION_HTTP_STATUS) == set(DOMAIN_EXCEPTION_MESSAGES)

    for exception_type, code in DOMAIN_EXCEPTION_ERROR_CODES.items():
        assert issubclass(exception_type, SafetyMainDomainError)
        assert code in PUBLIC_ERROR_CODES
        assert DOMAIN_EXCEPTION_MESSAGES[exception_type]
        assert DOMAIN_EXCEPTION_HTTP_STATUS[exception_type] >= 400


def test_required_task_error_codes_are_registered() -> None:
    required_codes = {
        "request_validation_error",
        "internal_server_error",
        "service_not_ready",
        "knowledge_object_not_found",
        "duplicate_knowledge_object",
        "knowledge_object_version_conflict",
        "knowledge_object_already_archived",
        "knowledge_object_already_active",
        "knowledge_object_already_deleted",
        "invalid_knowledge_object_state_transition",
        "knowledge_object_relation_not_found",
        "duplicate_knowledge_object_relation",
        "self_referencing_knowledge_object_relation",
    }
    assert required_codes.issubset(PUBLIC_ERROR_CODES)


def test_validation_message_is_stable() -> None:
    assert REQUEST_VALIDATION_MESSAGE == "The request is invalid."

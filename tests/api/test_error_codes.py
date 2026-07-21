from __future__ import annotations


from backend.api.error_codes import (
    DOMAIN_EXCEPTION_ERROR_CODES,
    DOMAIN_EXCEPTION_HTTP_STATUS,
    DOMAIN_EXCEPTION_MESSAGES,
    PUBLIC_ERROR_CODES,
    REQUEST_VALIDATION_ERROR,
    REQUEST_VALIDATION_MESSAGE,
)
from backend.core.application.exceptions.authentication import AuthenticationError
from backend.core.application.exceptions.authorization import AuthorizationError
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
        "unauthenticated",
        "invalid_credentials",
        "invalid_refresh_token",
        "authentication_forbidden",
        "organization_access_denied",
        "organization_context_required",
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


def test_authentication_exception_registry_is_complete() -> None:
    from backend.api.error_codes import (
        APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES,
        APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS,
        APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES,
    )

    assert set(APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS) == set(
        APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES
    )
    assert set(APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS) == set(
        APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES
    )

    for exception_type, code in APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES.items():
        assert issubclass(exception_type, AuthenticationError)
        assert code in PUBLIC_ERROR_CODES
        assert APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES[exception_type]
        assert APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS[exception_type] >= 400


def test_authorization_exception_registry_is_complete() -> None:
    from backend.api.error_codes import (
        APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES,
        APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS,
        APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES,
    )

    assert set(APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS) == set(
        APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES
    )
    assert set(APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS) == set(
        APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES
    )

    for exception_type, code in APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES.items():
        assert issubclass(exception_type, AuthorizationError)
        assert code in PUBLIC_ERROR_CODES
        assert APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES[exception_type]
        assert APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS[exception_type] >= 400


def test_validation_message_is_stable() -> None:
    assert REQUEST_VALIDATION_MESSAGE == "The request is invalid."

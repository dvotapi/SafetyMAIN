from __future__ import annotations

from backend.core.application.exceptions.authentication import (
    AuthenticationForbiddenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UnauthenticatedError,
)
from backend.core.application.exceptions.authorization import (
    MembershipRequiredError,
    OrganizationAccessDeniedError,
    OrganizationContextMismatchError,
    PermissionDeniedError,
)
from backend.core.domain.exceptions import (
    CrossOrganizationKnowledgeObjectRelation,
    DuplicateKnowledgeObject,
    DuplicateKnowledgeObjectRelation,
    DuplicateUserEmail,
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectAlreadyActive,
    KnowledgeObjectAlreadyArchived,
    KnowledgeObjectAlreadyDeleted,
    KnowledgeObjectNotFound,
    KnowledgeObjectRelationNotFound,
    KnowledgeObjectVersionConflict,
    SelfReferencingKnowledgeObjectRelation,
    UserAlreadyActive,
    UserAlreadyDeactivated,
    UserNotFound,
)

# Public API error codes (external contract). Do not derive these from class names.

KNOWLEDGE_OBJECT_NOT_FOUND = "knowledge_object_not_found"
DUPLICATE_KNOWLEDGE_OBJECT = "duplicate_knowledge_object"
KNOWLEDGE_OBJECT_VERSION_CONFLICT = "knowledge_object_version_conflict"
KNOWLEDGE_OBJECT_ALREADY_ARCHIVED = "knowledge_object_already_archived"
KNOWLEDGE_OBJECT_ALREADY_ACTIVE = "knowledge_object_already_active"
KNOWLEDGE_OBJECT_ALREADY_DELETED = "knowledge_object_already_deleted"
INVALID_KNOWLEDGE_OBJECT_STATE_TRANSITION = "invalid_knowledge_object_state_transition"

KNOWLEDGE_OBJECT_RELATION_NOT_FOUND = "knowledge_object_relation_not_found"
DUPLICATE_KNOWLEDGE_OBJECT_RELATION = "duplicate_knowledge_object_relation"
SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION = "self_referencing_knowledge_object_relation"
CROSS_ORGANIZATION_KNOWLEDGE_OBJECT_RELATION = (
    "cross_organization_knowledge_object_relation"
)

UNAUTHENTICATED = "unauthenticated"
INVALID_CREDENTIALS = "invalid_credentials"
INVALID_REFRESH_TOKEN = "invalid_refresh_token"
AUTHENTICATION_FORBIDDEN = "authentication_forbidden"
ORGANIZATION_ACCESS_DENIED = "organization_access_denied"
PERMISSION_DENIED = "permission_denied"
ORGANIZATION_CONTEXT_REQUIRED = "organization_context_required"

USER_NOT_FOUND = "user_not_found"
DUPLICATE_USER_EMAIL = "duplicate_user_email"
USER_ALREADY_ACTIVE = "user_already_active"
USER_ALREADY_DEACTIVATED = "user_already_deactivated"

REQUEST_VALIDATION_ERROR = "request_validation_error"
REQUEST_VALIDATION_MESSAGE = "The request is invalid."
SERVICE_NOT_READY = "service_not_ready"
INTERNAL_SERVER_ERROR = "internal_server_error"

PUBLIC_ERROR_CODES: frozenset[str] = frozenset(
    {
        KNOWLEDGE_OBJECT_NOT_FOUND,
        DUPLICATE_KNOWLEDGE_OBJECT,
        KNOWLEDGE_OBJECT_VERSION_CONFLICT,
        KNOWLEDGE_OBJECT_ALREADY_ARCHIVED,
        KNOWLEDGE_OBJECT_ALREADY_ACTIVE,
        KNOWLEDGE_OBJECT_ALREADY_DELETED,
        INVALID_KNOWLEDGE_OBJECT_STATE_TRANSITION,
        KNOWLEDGE_OBJECT_RELATION_NOT_FOUND,
        DUPLICATE_KNOWLEDGE_OBJECT_RELATION,
        SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION,
        CROSS_ORGANIZATION_KNOWLEDGE_OBJECT_RELATION,
        UNAUTHENTICATED,
        INVALID_CREDENTIALS,
        INVALID_REFRESH_TOKEN,
        AUTHENTICATION_FORBIDDEN,
        ORGANIZATION_ACCESS_DENIED,
        PERMISSION_DENIED,
        ORGANIZATION_CONTEXT_REQUIRED,
        USER_NOT_FOUND,
        DUPLICATE_USER_EMAIL,
        USER_ALREADY_ACTIVE,
        USER_ALREADY_DEACTIVATED,
        REQUEST_VALIDATION_ERROR,
        SERVICE_NOT_READY,
        INTERNAL_SERVER_ERROR,
    }
)

DOMAIN_EXCEPTION_HTTP_STATUS: dict[type[Exception], int] = {
    KnowledgeObjectNotFound: 404,
    DuplicateKnowledgeObject: 409,
    KnowledgeObjectVersionConflict: 409,
    KnowledgeObjectAlreadyArchived: 409,
    KnowledgeObjectAlreadyActive: 409,
    KnowledgeObjectAlreadyDeleted: 409,
    InvalidKnowledgeObjectStateTransition: 409,
    KnowledgeObjectRelationNotFound: 404,
    DuplicateKnowledgeObjectRelation: 409,
    SelfReferencingKnowledgeObjectRelation: 422,
    CrossOrganizationKnowledgeObjectRelation: 422,
    UserNotFound: 404,
    DuplicateUserEmail: 409,
    UserAlreadyActive: 409,
    UserAlreadyDeactivated: 409,
}

DOMAIN_EXCEPTION_ERROR_CODES: dict[type[Exception], str] = {
    KnowledgeObjectNotFound: KNOWLEDGE_OBJECT_NOT_FOUND,
    DuplicateKnowledgeObject: DUPLICATE_KNOWLEDGE_OBJECT,
    KnowledgeObjectVersionConflict: KNOWLEDGE_OBJECT_VERSION_CONFLICT,
    KnowledgeObjectAlreadyArchived: KNOWLEDGE_OBJECT_ALREADY_ARCHIVED,
    KnowledgeObjectAlreadyActive: KNOWLEDGE_OBJECT_ALREADY_ACTIVE,
    KnowledgeObjectAlreadyDeleted: KNOWLEDGE_OBJECT_ALREADY_DELETED,
    InvalidKnowledgeObjectStateTransition: INVALID_KNOWLEDGE_OBJECT_STATE_TRANSITION,
    KnowledgeObjectRelationNotFound: KNOWLEDGE_OBJECT_RELATION_NOT_FOUND,
    DuplicateKnowledgeObjectRelation: DUPLICATE_KNOWLEDGE_OBJECT_RELATION,
    SelfReferencingKnowledgeObjectRelation: SELF_REFERENCING_KNOWLEDGE_OBJECT_RELATION,
    CrossOrganizationKnowledgeObjectRelation: CROSS_ORGANIZATION_KNOWLEDGE_OBJECT_RELATION,
    UserNotFound: USER_NOT_FOUND,
    DuplicateUserEmail: DUPLICATE_USER_EMAIL,
    UserAlreadyActive: USER_ALREADY_ACTIVE,
    UserAlreadyDeactivated: USER_ALREADY_DEACTIVATED,
}

DOMAIN_EXCEPTION_MESSAGES: dict[type[Exception], str] = {
    KnowledgeObjectNotFound: "Knowledge Object was not found.",
    DuplicateKnowledgeObject: "Knowledge Object already exists.",
    KnowledgeObjectVersionConflict: "Knowledge Object version conflict.",
    KnowledgeObjectAlreadyArchived: "Knowledge Object is already archived.",
    KnowledgeObjectAlreadyActive: "Knowledge Object is already active.",
    KnowledgeObjectAlreadyDeleted: "Knowledge Object is already deleted.",
    InvalidKnowledgeObjectStateTransition: "Invalid Knowledge Object state transition.",
    KnowledgeObjectRelationNotFound: "Knowledge Object Relation was not found.",
    DuplicateKnowledgeObjectRelation: "Knowledge Object Relation already exists.",
    SelfReferencingKnowledgeObjectRelation: (
        "Knowledge Object Relation cannot reference itself."
    ),
    CrossOrganizationKnowledgeObjectRelation: (
        "Knowledge Object Relation cannot cross organizations."
    ),
    UserNotFound: "User was not found.",
    DuplicateUserEmail: "User email already exists.",
    UserAlreadyActive: "User is already active.",
    UserAlreadyDeactivated: "User is already deactivated.",
}

APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS: dict[type[Exception], int] = {
    UnauthenticatedError: 401,
    InvalidCredentialsError: 401,
    InvalidRefreshTokenError: 401,
    AuthenticationForbiddenError: 403,
}

APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES: dict[type[Exception], str] = {
    UnauthenticatedError: UNAUTHENTICATED,
    InvalidCredentialsError: INVALID_CREDENTIALS,
    InvalidRefreshTokenError: INVALID_REFRESH_TOKEN,
    AuthenticationForbiddenError: AUTHENTICATION_FORBIDDEN,
}

APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES: dict[type[Exception], str] = {
    UnauthenticatedError: "Authentication is required.",
    InvalidCredentialsError: "Invalid email or password.",
    InvalidRefreshTokenError: "The refresh token is invalid or expired.",
    AuthenticationForbiddenError: "The user account cannot authenticate.",
}

APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS: dict[type[Exception], int] = {
    OrganizationAccessDeniedError: 403,
    PermissionDeniedError: 403,
    MembershipRequiredError: 422,
    OrganizationContextMismatchError: 422,
}

APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES: dict[type[Exception], str] = {
    OrganizationAccessDeniedError: ORGANIZATION_ACCESS_DENIED,
    PermissionDeniedError: PERMISSION_DENIED,
    MembershipRequiredError: ORGANIZATION_CONTEXT_REQUIRED,
    OrganizationContextMismatchError: ORGANIZATION_CONTEXT_REQUIRED,
}

APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES: dict[type[Exception], str] = {
    OrganizationAccessDeniedError: "Organization access was denied.",
    PermissionDeniedError: "Permission was denied.",
    MembershipRequiredError: "Organization membership context is required.",
    OrganizationContextMismatchError: "Organization membership context is required.",
}

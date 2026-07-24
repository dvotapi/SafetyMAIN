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
from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    InvalidRiskControlTransition,
    RiskControlAlreadyMaterialized,
    RiskControlCannotBeModified,
    RiskControlNotFound,
    RiskControlReasonRequired,
    RiskControlValidationError,
    RiskControlVersionConflict,
)
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    InvalidAssessmentProfile,
    InvalidRiskAssessmentTransition,
    InvalidRiskEvaluation,
    RiskAssessmentAcceptanceRequired,
    RiskAssessmentAlreadyApproved,
    RiskAssessmentAlreadyArchived,
    RiskAssessmentArchiveReasonRequired,
    RiskAssessmentCannotBeModified,
    RiskAssessmentHazardNotActive,
    RiskAssessmentInherentRiskRequired,
    RiskAssessmentNotFound,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.exceptions.hazard import (
    DuplicateHazardCode,
    HazardAlreadyActive,
    HazardAlreadyArchived,
    HazardArchiveReasonRequired,
    HazardCannotBeModified,
    HazardCategoryRequired,
    HazardNotArchived,
    HazardNotFound,
    HazardRestoreReasonRequired,
    HazardSafetyDirectionRequired,
    HazardTitleRequired,
    HazardVersionConflict,
    InvalidAffectedSubject,
    InvalidHazardCategory,
    InvalidHazardSource,
    InvalidHazardTransition,
    InvalidSafetyDirection,
)
from backend.core.domain.exceptions import (
    CrossOrganizationKnowledgeObjectRelation,
    DuplicateKnowledgeObject,
    DuplicateKnowledgeObjectRelation,
    DuplicateUserEmail,
    CurrentOrganizationDeactivationError,
    DuplicateMembership,
    DuplicateOrganizationName,
    DuplicateActiveInvitation,
    ExistingActiveMembership,
    InvalidMembershipRole,
    InvitationAlreadyAccepted,
    InvitationAlreadyRevoked,
    InvitationEmailMismatch,
    InvitationExpired,
    InvitationNotFound,
    InvitationTokenInvalid,
    AuditEventNotFound,
    LastOrganizationAdministratorError,
    MembershipAlreadyActive,
    MembershipAlreadyInactive,
    MembershipByIdNotFound,
    OrganizationAlreadyActive,
    OrganizationAlreadyInactive,
    OrganizationNotFound,
    SelfMembershipDeactivationError,
    SelfMembershipRoleDowngradeError,
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

ORGANIZATION_NOT_FOUND = "organization_not_found"
DUPLICATE_ORGANIZATION_NAME = "duplicate_organization_name"
ORGANIZATION_ALREADY_ACTIVE = "organization_already_active"
ORGANIZATION_ALREADY_INACTIVE = "organization_already_inactive"
CURRENT_ORGANIZATION_DEACTIVATION = "current_organization_deactivation"

MEMBERSHIP_NOT_FOUND = "membership_not_found"
DUPLICATE_MEMBERSHIP = "duplicate_membership"
MEMBERSHIP_ALREADY_ACTIVE = "membership_already_active"
MEMBERSHIP_ALREADY_INACTIVE = "membership_already_inactive"
SELF_MEMBERSHIP_DEACTIVATION = "self_membership_deactivation"
SELF_MEMBERSHIP_ROLE_DOWNGRADE = "self_membership_role_downgrade"
LAST_ORGANIZATION_ADMINISTRATOR = "last_organization_administrator"
INVALID_MEMBERSHIP_ROLE = "invalid_membership_role"

INVITATION_NOT_FOUND = "invitation_not_found"
DUPLICATE_ACTIVE_INVITATION = "duplicate_active_invitation"
EXISTING_ACTIVE_MEMBERSHIP = "existing_active_membership"
INVITATION_ALREADY_ACCEPTED = "invitation_already_accepted"
INVITATION_ALREADY_REVOKED = "invitation_already_revoked"
INVITATION_EXPIRED = "invitation_expired"
INVITATION_TOKEN_INVALID = "invitation_token_invalid"
INVITATION_EMAIL_MISMATCH = "invitation_email_mismatch"
AUDIT_EVENT_NOT_FOUND = "audit_event_not_found"

HAZARD_NOT_FOUND = "hazard_not_found"
DUPLICATE_HAZARD_CODE = "duplicate_hazard_code"
HAZARD_VERSION_CONFLICT = "hazard_version_conflict"
HAZARD_ALREADY_ACTIVE = "hazard_already_active"
HAZARD_ALREADY_ARCHIVED = "hazard_already_archived"
HAZARD_NOT_ARCHIVED = "hazard_not_archived"
INVALID_HAZARD_TRANSITION = "invalid_hazard_transition"
HAZARD_CANNOT_BE_MODIFIED = "hazard_cannot_be_modified"
HAZARD_TITLE_REQUIRED = "hazard_title_required"
HAZARD_CATEGORY_REQUIRED = "hazard_category_required"
HAZARD_SAFETY_DIRECTION_REQUIRED = "hazard_safety_direction_required"
INVALID_HAZARD_CATEGORY = "invalid_hazard_category"
INVALID_SAFETY_DIRECTION = "invalid_safety_direction"
INVALID_HAZARD_SOURCE = "invalid_hazard_source"
INVALID_AFFECTED_SUBJECT = "invalid_affected_subject"
HAZARD_ARCHIVE_REASON_REQUIRED = "hazard_archive_reason_required"
HAZARD_RESTORE_REASON_REQUIRED = "hazard_restore_reason_required"

RISK_ASSESSMENT_NOT_FOUND = "risk_assessment_not_found"
DUPLICATE_RISK_ASSESSMENT_CODE = "duplicate_risk_assessment_code"
RISK_ASSESSMENT_VERSION_CONFLICT = "risk_assessment_version_conflict"
INVALID_RISK_ASSESSMENT_TRANSITION = "invalid_risk_assessment_transition"
RISK_ASSESSMENT_CANNOT_BE_MODIFIED = "risk_assessment_cannot_be_modified"
RISK_ASSESSMENT_HAZARD_NOT_ACTIVE = "risk_assessment_hazard_not_active"
RISK_ASSESSMENT_INHERENT_RISK_REQUIRED = "risk_assessment_inherent_risk_required"
RISK_ASSESSMENT_ACCEPTANCE_REQUIRED = "risk_assessment_acceptance_required"
INVALID_ASSESSMENT_PROFILE = "invalid_assessment_profile"
INVALID_RISK_EVALUATION = "invalid_risk_evaluation"
RISK_ASSESSMENT_ALREADY_APPROVED = "risk_assessment_already_approved"
RISK_ASSESSMENT_ALREADY_ARCHIVED = "risk_assessment_already_archived"
RISK_ASSESSMENT_ARCHIVE_REASON_REQUIRED = "risk_assessment_archive_reason_required"
RISK_CONTROL_NOT_FOUND = "risk_control_not_found"
DUPLICATE_RISK_CONTROL_CODE = "duplicate_risk_control_code"
RISK_CONTROL_VERSION_CONFLICT = "risk_control_version_conflict"
RISK_CONTROL_ALREADY_MATERIALIZED = "risk_control_already_materialized"
INVALID_RISK_CONTROL_TRANSITION = "invalid_risk_control_transition"
RISK_CONTROL_VALIDATION_ERROR = "risk_control_validation_error"
RISK_CONTROL_CANNOT_BE_MODIFIED = "risk_control_cannot_be_modified"
RISK_CONTROL_REASON_REQUIRED = "risk_control_reason_required"

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
        ORGANIZATION_NOT_FOUND,
        DUPLICATE_ORGANIZATION_NAME,
        ORGANIZATION_ALREADY_ACTIVE,
        ORGANIZATION_ALREADY_INACTIVE,
        CURRENT_ORGANIZATION_DEACTIVATION,
        MEMBERSHIP_NOT_FOUND,
        DUPLICATE_MEMBERSHIP,
        MEMBERSHIP_ALREADY_ACTIVE,
        MEMBERSHIP_ALREADY_INACTIVE,
        SELF_MEMBERSHIP_DEACTIVATION,
        SELF_MEMBERSHIP_ROLE_DOWNGRADE,
        LAST_ORGANIZATION_ADMINISTRATOR,
        INVALID_MEMBERSHIP_ROLE,
        INVITATION_NOT_FOUND,
        DUPLICATE_ACTIVE_INVITATION,
        EXISTING_ACTIVE_MEMBERSHIP,
        INVITATION_ALREADY_ACCEPTED,
        INVITATION_ALREADY_REVOKED,
        INVITATION_EXPIRED,
        INVITATION_TOKEN_INVALID,
        INVITATION_EMAIL_MISMATCH,
        AUDIT_EVENT_NOT_FOUND,
        HAZARD_NOT_FOUND,
        DUPLICATE_HAZARD_CODE,
        HAZARD_VERSION_CONFLICT,
        HAZARD_ALREADY_ACTIVE,
        HAZARD_ALREADY_ARCHIVED,
        HAZARD_NOT_ARCHIVED,
        INVALID_HAZARD_TRANSITION,
        HAZARD_CANNOT_BE_MODIFIED,
        HAZARD_TITLE_REQUIRED,
        HAZARD_CATEGORY_REQUIRED,
        HAZARD_SAFETY_DIRECTION_REQUIRED,
        INVALID_HAZARD_CATEGORY,
        INVALID_SAFETY_DIRECTION,
        INVALID_HAZARD_SOURCE,
        INVALID_AFFECTED_SUBJECT,
        HAZARD_ARCHIVE_REASON_REQUIRED,
        HAZARD_RESTORE_REASON_REQUIRED,
        RISK_ASSESSMENT_NOT_FOUND,
        DUPLICATE_RISK_ASSESSMENT_CODE,
        RISK_ASSESSMENT_VERSION_CONFLICT,
        INVALID_RISK_ASSESSMENT_TRANSITION,
        RISK_ASSESSMENT_CANNOT_BE_MODIFIED,
        RISK_ASSESSMENT_HAZARD_NOT_ACTIVE,
        RISK_ASSESSMENT_INHERENT_RISK_REQUIRED,
        RISK_ASSESSMENT_ACCEPTANCE_REQUIRED,
        INVALID_ASSESSMENT_PROFILE,
        INVALID_RISK_EVALUATION,
        RISK_ASSESSMENT_ALREADY_APPROVED,
        RISK_ASSESSMENT_ALREADY_ARCHIVED,
        RISK_ASSESSMENT_ARCHIVE_REASON_REQUIRED,
        RISK_CONTROL_NOT_FOUND,
        DUPLICATE_RISK_CONTROL_CODE,
        RISK_CONTROL_VERSION_CONFLICT,
        RISK_CONTROL_ALREADY_MATERIALIZED,
        INVALID_RISK_CONTROL_TRANSITION,
        RISK_CONTROL_VALIDATION_ERROR,
        RISK_CONTROL_CANNOT_BE_MODIFIED,
        RISK_CONTROL_REASON_REQUIRED,
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
    OrganizationNotFound: 404,
    DuplicateOrganizationName: 409,
    OrganizationAlreadyActive: 409,
    OrganizationAlreadyInactive: 409,
    CurrentOrganizationDeactivationError: 409,
    MembershipByIdNotFound: 404,
    DuplicateMembership: 409,
    MembershipAlreadyActive: 409,
    MembershipAlreadyInactive: 409,
    SelfMembershipDeactivationError: 409,
    SelfMembershipRoleDowngradeError: 409,
    LastOrganizationAdministratorError: 409,
    InvalidMembershipRole: 422,
    InvitationNotFound: 404,
    DuplicateActiveInvitation: 409,
    ExistingActiveMembership: 409,
    InvitationAlreadyAccepted: 409,
    InvitationAlreadyRevoked: 409,
    InvitationExpired: 409,
    InvitationTokenInvalid: 400,
    InvitationEmailMismatch: 403,
    AuditEventNotFound: 404,
    HazardNotFound: 404,
    DuplicateHazardCode: 409,
    HazardVersionConflict: 409,
    HazardAlreadyActive: 409,
    HazardAlreadyArchived: 409,
    HazardNotArchived: 422,
    InvalidHazardTransition: 422,
    HazardCannotBeModified: 422,
    HazardTitleRequired: 422,
    HazardCategoryRequired: 422,
    HazardSafetyDirectionRequired: 422,
    InvalidHazardCategory: 422,
    InvalidSafetyDirection: 422,
    InvalidHazardSource: 422,
    InvalidAffectedSubject: 422,
    HazardArchiveReasonRequired: 422,
    HazardRestoreReasonRequired: 422,
    RiskAssessmentNotFound: 404,
    DuplicateRiskAssessmentCode: 409,
    RiskAssessmentVersionConflict: 409,
    InvalidRiskAssessmentTransition: 422,
    RiskAssessmentCannotBeModified: 422,
    RiskAssessmentHazardNotActive: 422,
    RiskAssessmentInherentRiskRequired: 422,
    RiskAssessmentAcceptanceRequired: 422,
    InvalidAssessmentProfile: 422,
    InvalidRiskEvaluation: 422,
    RiskAssessmentAlreadyApproved: 409,
    RiskAssessmentAlreadyArchived: 409,
    RiskAssessmentArchiveReasonRequired: 422,
    RiskControlNotFound: 404,
    DuplicateRiskControlCode: 409,
    RiskControlVersionConflict: 409,
    RiskControlAlreadyMaterialized: 409,
    InvalidRiskControlTransition: 422,
    RiskControlValidationError: 422,
    RiskControlCannotBeModified: 422,
    RiskControlReasonRequired: 422,
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
    OrganizationNotFound: ORGANIZATION_NOT_FOUND,
    DuplicateOrganizationName: DUPLICATE_ORGANIZATION_NAME,
    OrganizationAlreadyActive: ORGANIZATION_ALREADY_ACTIVE,
    OrganizationAlreadyInactive: ORGANIZATION_ALREADY_INACTIVE,
    CurrentOrganizationDeactivationError: CURRENT_ORGANIZATION_DEACTIVATION,
    MembershipByIdNotFound: MEMBERSHIP_NOT_FOUND,
    DuplicateMembership: DUPLICATE_MEMBERSHIP,
    MembershipAlreadyActive: MEMBERSHIP_ALREADY_ACTIVE,
    MembershipAlreadyInactive: MEMBERSHIP_ALREADY_INACTIVE,
    SelfMembershipDeactivationError: SELF_MEMBERSHIP_DEACTIVATION,
    SelfMembershipRoleDowngradeError: SELF_MEMBERSHIP_ROLE_DOWNGRADE,
    LastOrganizationAdministratorError: LAST_ORGANIZATION_ADMINISTRATOR,
    InvalidMembershipRole: INVALID_MEMBERSHIP_ROLE,
    InvitationNotFound: INVITATION_NOT_FOUND,
    DuplicateActiveInvitation: DUPLICATE_ACTIVE_INVITATION,
    ExistingActiveMembership: EXISTING_ACTIVE_MEMBERSHIP,
    InvitationAlreadyAccepted: INVITATION_ALREADY_ACCEPTED,
    InvitationAlreadyRevoked: INVITATION_ALREADY_REVOKED,
    InvitationExpired: INVITATION_EXPIRED,
    InvitationTokenInvalid: INVITATION_TOKEN_INVALID,
    InvitationEmailMismatch: INVITATION_EMAIL_MISMATCH,
    AuditEventNotFound: AUDIT_EVENT_NOT_FOUND,
    HazardNotFound: HAZARD_NOT_FOUND,
    DuplicateHazardCode: DUPLICATE_HAZARD_CODE,
    HazardVersionConflict: HAZARD_VERSION_CONFLICT,
    HazardAlreadyActive: HAZARD_ALREADY_ACTIVE,
    HazardAlreadyArchived: HAZARD_ALREADY_ARCHIVED,
    HazardNotArchived: HAZARD_NOT_ARCHIVED,
    InvalidHazardTransition: INVALID_HAZARD_TRANSITION,
    HazardCannotBeModified: HAZARD_CANNOT_BE_MODIFIED,
    HazardTitleRequired: HAZARD_TITLE_REQUIRED,
    HazardCategoryRequired: HAZARD_CATEGORY_REQUIRED,
    HazardSafetyDirectionRequired: HAZARD_SAFETY_DIRECTION_REQUIRED,
    InvalidHazardCategory: INVALID_HAZARD_CATEGORY,
    InvalidSafetyDirection: INVALID_SAFETY_DIRECTION,
    InvalidHazardSource: INVALID_HAZARD_SOURCE,
    InvalidAffectedSubject: INVALID_AFFECTED_SUBJECT,
    HazardArchiveReasonRequired: HAZARD_ARCHIVE_REASON_REQUIRED,
    HazardRestoreReasonRequired: HAZARD_RESTORE_REASON_REQUIRED,
    RiskAssessmentNotFound: RISK_ASSESSMENT_NOT_FOUND,
    DuplicateRiskAssessmentCode: DUPLICATE_RISK_ASSESSMENT_CODE,
    RiskAssessmentVersionConflict: RISK_ASSESSMENT_VERSION_CONFLICT,
    InvalidRiskAssessmentTransition: INVALID_RISK_ASSESSMENT_TRANSITION,
    RiskAssessmentCannotBeModified: RISK_ASSESSMENT_CANNOT_BE_MODIFIED,
    RiskAssessmentHazardNotActive: RISK_ASSESSMENT_HAZARD_NOT_ACTIVE,
    RiskAssessmentInherentRiskRequired: RISK_ASSESSMENT_INHERENT_RISK_REQUIRED,
    RiskAssessmentAcceptanceRequired: RISK_ASSESSMENT_ACCEPTANCE_REQUIRED,
    InvalidAssessmentProfile: INVALID_ASSESSMENT_PROFILE,
    InvalidRiskEvaluation: INVALID_RISK_EVALUATION,
    RiskAssessmentAlreadyApproved: RISK_ASSESSMENT_ALREADY_APPROVED,
    RiskAssessmentAlreadyArchived: RISK_ASSESSMENT_ALREADY_ARCHIVED,
    RiskAssessmentArchiveReasonRequired: RISK_ASSESSMENT_ARCHIVE_REASON_REQUIRED,
    RiskControlNotFound: RISK_CONTROL_NOT_FOUND,
    DuplicateRiskControlCode: DUPLICATE_RISK_CONTROL_CODE,
    RiskControlVersionConflict: RISK_CONTROL_VERSION_CONFLICT,
    RiskControlAlreadyMaterialized: RISK_CONTROL_ALREADY_MATERIALIZED,
    InvalidRiskControlTransition: INVALID_RISK_CONTROL_TRANSITION,
    RiskControlValidationError: RISK_CONTROL_VALIDATION_ERROR,
    RiskControlCannotBeModified: RISK_CONTROL_CANNOT_BE_MODIFIED,
    RiskControlReasonRequired: RISK_CONTROL_REASON_REQUIRED,
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
    OrganizationNotFound: "Organization was not found.",
    DuplicateOrganizationName: "Organization name already exists.",
    OrganizationAlreadyActive: "Organization is already active.",
    OrganizationAlreadyInactive: "Organization is already inactive.",
    CurrentOrganizationDeactivationError: (
        "The current authorization organization cannot be deactivated."
    ),
    MembershipByIdNotFound: "Organization membership was not found.",
    DuplicateMembership: "Organization membership already exists.",
    MembershipAlreadyActive: "Organization membership is already active.",
    MembershipAlreadyInactive: "Organization membership is already inactive.",
    SelfMembershipDeactivationError: (
        "The current authorization membership cannot be deactivated."
    ),
    SelfMembershipRoleDowngradeError: (
        "The current authorization membership role cannot be downgraded."
    ),
    LastOrganizationAdministratorError: (
        "Organization must retain at least one active administrator."
    ),
    InvalidMembershipRole: "Membership role is invalid.",
    InvitationNotFound: "Invitation was not found.",
    DuplicateActiveInvitation: "An active invitation already exists for this organization and email.",
    ExistingActiveMembership: "User already has an active membership in the target organization.",
    InvitationAlreadyAccepted: "Invitation has already been accepted.",
    InvitationAlreadyRevoked: "Invitation has already been revoked.",
    InvitationExpired: "Invitation has expired.",
    InvitationTokenInvalid: "Invitation token is invalid.",
    InvitationEmailMismatch: "Authenticated user email does not match the invitation.",
    AuditEventNotFound: "Audit event was not found.",
    HazardNotFound: "Hazard was not found.",
    DuplicateHazardCode: "Hazard code already exists.",
    HazardVersionConflict: "Hazard version conflict.",
    HazardAlreadyActive: "Hazard is already active.",
    HazardAlreadyArchived: "Hazard is already archived.",
    HazardNotArchived: "Hazard is not archived.",
    InvalidHazardTransition: "Invalid hazard lifecycle transition.",
    HazardCannotBeModified: "Hazard cannot be modified.",
    HazardTitleRequired: "Hazard title is required.",
    HazardCategoryRequired: "Hazard category is required.",
    HazardSafetyDirectionRequired: "At least one safety direction is required.",
    InvalidHazardCategory: "Invalid hazard category.",
    InvalidSafetyDirection: "Invalid safety direction.",
    InvalidHazardSource: "Invalid hazard source.",
    InvalidAffectedSubject: "Invalid affected subject.",
    HazardArchiveReasonRequired: "Archive reason is required.",
    HazardRestoreReasonRequired: "Restore reason is required.",
    RiskAssessmentNotFound: "Risk assessment was not found.",
    DuplicateRiskAssessmentCode: "Risk assessment code already exists.",
    RiskAssessmentVersionConflict: "Risk assessment version conflict.",
    InvalidRiskAssessmentTransition: "Invalid risk assessment lifecycle transition.",
    RiskAssessmentCannotBeModified: "Risk assessment cannot be modified.",
    RiskAssessmentHazardNotActive: "Risk assessments require an active hazard.",
    RiskAssessmentInherentRiskRequired: "Inherent risk evaluation is required.",
    RiskAssessmentAcceptanceRequired: "Risk acceptance decision is required.",
    InvalidAssessmentProfile: "Invalid assessment profile.",
    InvalidRiskEvaluation: "Invalid risk evaluation.",
    RiskAssessmentAlreadyApproved: "Risk assessment is already approved.",
    RiskAssessmentAlreadyArchived: "Risk assessment is already archived.",
    RiskAssessmentArchiveReasonRequired: "Archive reason is required.",
    RiskControlNotFound: "Risk control was not found.",
    DuplicateRiskControlCode: "Risk control code already exists.",
    RiskControlVersionConflict: "Risk control version conflict.",
    RiskControlAlreadyMaterialized: "Risk control already materialized for source reference.",
    InvalidRiskControlTransition: "Invalid risk control lifecycle transition.",
    RiskControlValidationError: "Risk control validation failed.",
    RiskControlCannotBeModified: "Risk control cannot be modified.",
    RiskControlReasonRequired: "A reason is required for this risk control action.",
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

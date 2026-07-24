from __future__ import annotations

from backend.core.domain.exceptions import (
    CurrentOrganizationDeactivationError,
    DuplicateMembership,
    DuplicateOrganizationName,
    DuplicateUserEmail,
    InvalidMembershipRole,
    LastOrganizationAdministratorError,
    MembershipAlreadyActive,
    MembershipAlreadyInactive,
    OrganizationAlreadyActive,
    OrganizationAlreadyInactive,
    SelfMembershipDeactivationError,
    SelfMembershipRoleDowngradeError,
    UserAlreadyActive,
    UserAlreadyDeactivated,
)
from backend.core.domain.exceptions.hazard import (
    DuplicateHazardCode,
    HazardAlreadyActive,
    HazardAlreadyArchived,
    HazardCannotBeModified,
    HazardNotArchived,
    HazardVersionConflict,
    InvalidHazardTransition,
)
from backend.core.domain.exceptions.invitation import (
    DuplicateActiveInvitation,
    ExistingActiveMembership,
    InvitationAlreadyAccepted,
    InvitationAlreadyRevoked,
    InvitationEmailMismatch,
    InvitationExpired,
    InvitationTokenInvalid,
)
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    InvalidRiskAssessmentTransition,
    RiskAssessmentAlreadyApproved,
    RiskAssessmentAlreadyArchived,
    RiskAssessmentCannotBeModified,
    RiskAssessmentHazardNotActive,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    InvalidRiskControlTransition,
    RiskControlAlreadyMaterialized,
    RiskControlCannotBeModified,
    RiskControlVersionConflict,
)

DUPLICATE_USER_EMAIL = "duplicate_user_email"
USER_ALREADY_ACTIVE = "user_already_active"
USER_ALREADY_DEACTIVATED = "user_already_deactivated"
DUPLICATE_ORGANIZATION_NAME = "duplicate_organization_name"
ORGANIZATION_ALREADY_ACTIVE = "organization_already_active"
ORGANIZATION_ALREADY_INACTIVE = "organization_already_inactive"
CURRENT_ORGANIZATION_DEACTIVATION = "current_organization_deactivation"
DUPLICATE_MEMBERSHIP = "duplicate_membership"
MEMBERSHIP_ALREADY_ACTIVE = "membership_already_active"
MEMBERSHIP_ALREADY_INACTIVE = "membership_already_inactive"
SELF_MEMBERSHIP_DEACTIVATION = "self_membership_deactivation"
SELF_MEMBERSHIP_ROLE_DOWNGRADE = "self_membership_role_downgrade"
LAST_ORGANIZATION_ADMINISTRATOR = "last_organization_administrator"
INVALID_MEMBERSHIP_ROLE = "invalid_membership_role"
DUPLICATE_ACTIVE_INVITATION = "duplicate_active_invitation"
EXISTING_ACTIVE_MEMBERSHIP = "existing_active_membership"
INVITATION_ALREADY_ACCEPTED = "invitation_already_accepted"
INVITATION_ALREADY_REVOKED = "invitation_already_revoked"
INVITATION_EXPIRED = "invitation_expired"
INVITATION_TOKEN_INVALID = "invitation_token_invalid"
INVITATION_EMAIL_MISMATCH = "invitation_email_mismatch"
DUPLICATE_HAZARD_CODE = "duplicate_hazard_code"
HAZARD_VERSION_CONFLICT = "hazard_version_conflict"
HAZARD_ALREADY_ACTIVE = "hazard_already_active"
HAZARD_ALREADY_ARCHIVED = "hazard_already_archived"
HAZARD_NOT_ARCHIVED = "hazard_not_archived"
INVALID_HAZARD_TRANSITION = "invalid_hazard_transition"
HAZARD_CANNOT_BE_MODIFIED = "hazard_cannot_be_modified"
DUPLICATE_RISK_ASSESSMENT_CODE = "duplicate_risk_assessment_code"
RISK_ASSESSMENT_VERSION_CONFLICT = "risk_assessment_version_conflict"
RISK_ASSESSMENT_ALREADY_APPROVED = "risk_assessment_already_approved"
RISK_ASSESSMENT_ALREADY_ARCHIVED = "risk_assessment_already_archived"
RISK_ASSESSMENT_CANNOT_BE_MODIFIED = "risk_assessment_cannot_be_modified"
RISK_ASSESSMENT_HAZARD_NOT_ACTIVE = "risk_assessment_hazard_not_active"
INVALID_RISK_ASSESSMENT_TRANSITION = "invalid_risk_assessment_transition"
DUPLICATE_RISK_CONTROL_CODE = "duplicate_risk_control_code"
RISK_CONTROL_VERSION_CONFLICT = "risk_control_version_conflict"
RISK_CONTROL_ALREADY_MATERIALIZED = "risk_control_already_materialized"
INVALID_RISK_CONTROL_TRANSITION = "invalid_risk_control_transition"
RISK_CONTROL_CANNOT_BE_MODIFIED = "risk_control_cannot_be_modified"

AUDITABLE_ADMIN_FAILURES: dict[type[Exception], str] = {
    DuplicateUserEmail: DUPLICATE_USER_EMAIL,
    UserAlreadyActive: USER_ALREADY_ACTIVE,
    UserAlreadyDeactivated: USER_ALREADY_DEACTIVATED,
    DuplicateOrganizationName: DUPLICATE_ORGANIZATION_NAME,
    OrganizationAlreadyActive: ORGANIZATION_ALREADY_ACTIVE,
    OrganizationAlreadyInactive: ORGANIZATION_ALREADY_INACTIVE,
    CurrentOrganizationDeactivationError: CURRENT_ORGANIZATION_DEACTIVATION,
    DuplicateMembership: DUPLICATE_MEMBERSHIP,
    MembershipAlreadyActive: MEMBERSHIP_ALREADY_ACTIVE,
    MembershipAlreadyInactive: MEMBERSHIP_ALREADY_INACTIVE,
    InvalidMembershipRole: INVALID_MEMBERSHIP_ROLE,
    SelfMembershipDeactivationError: SELF_MEMBERSHIP_DEACTIVATION,
    SelfMembershipRoleDowngradeError: SELF_MEMBERSHIP_ROLE_DOWNGRADE,
    LastOrganizationAdministratorError: LAST_ORGANIZATION_ADMINISTRATOR,
    DuplicateActiveInvitation: DUPLICATE_ACTIVE_INVITATION,
    ExistingActiveMembership: EXISTING_ACTIVE_MEMBERSHIP,
    InvitationAlreadyAccepted: INVITATION_ALREADY_ACCEPTED,
    InvitationAlreadyRevoked: INVITATION_ALREADY_REVOKED,
    InvitationExpired: INVITATION_EXPIRED,
    InvitationTokenInvalid: INVITATION_TOKEN_INVALID,
    InvitationEmailMismatch: INVITATION_EMAIL_MISMATCH,
    DuplicateHazardCode: DUPLICATE_HAZARD_CODE,
    HazardVersionConflict: HAZARD_VERSION_CONFLICT,
    HazardAlreadyActive: HAZARD_ALREADY_ACTIVE,
    HazardAlreadyArchived: HAZARD_ALREADY_ARCHIVED,
    HazardNotArchived: HAZARD_NOT_ARCHIVED,
    InvalidHazardTransition: INVALID_HAZARD_TRANSITION,
    HazardCannotBeModified: HAZARD_CANNOT_BE_MODIFIED,
    DuplicateRiskAssessmentCode: DUPLICATE_RISK_ASSESSMENT_CODE,
    RiskAssessmentVersionConflict: RISK_ASSESSMENT_VERSION_CONFLICT,
    RiskAssessmentAlreadyApproved: RISK_ASSESSMENT_ALREADY_APPROVED,
    RiskAssessmentAlreadyArchived: RISK_ASSESSMENT_ALREADY_ARCHIVED,
    RiskAssessmentCannotBeModified: RISK_ASSESSMENT_CANNOT_BE_MODIFIED,
    RiskAssessmentHazardNotActive: RISK_ASSESSMENT_HAZARD_NOT_ACTIVE,
    InvalidRiskAssessmentTransition: INVALID_RISK_ASSESSMENT_TRANSITION,
    DuplicateRiskControlCode: DUPLICATE_RISK_CONTROL_CODE,
    RiskControlVersionConflict: RISK_CONTROL_VERSION_CONFLICT,
    RiskControlAlreadyMaterialized: RISK_CONTROL_ALREADY_MATERIALIZED,
    InvalidRiskControlTransition: INVALID_RISK_CONTROL_TRANSITION,
    RiskControlCannotBeModified: RISK_CONTROL_CANNOT_BE_MODIFIED,
}

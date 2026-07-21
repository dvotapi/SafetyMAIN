from __future__ import annotations

from backend.core.domain.exceptions import (
    CurrentOrganizationDeactivationError,
    DuplicateMembership,
    DuplicateOrganizationName,
    DuplicateUserEmail,
    InvalidMembershipRole,
    LastOrganizationAdministratorError,
    OrganizationAlreadyActive,
    OrganizationAlreadyInactive,
    MembershipAlreadyActive,
    MembershipAlreadyInactive,
    SelfMembershipDeactivationError,
    SelfMembershipRoleDowngradeError,
    UserAlreadyActive,
    UserAlreadyDeactivated,
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
}

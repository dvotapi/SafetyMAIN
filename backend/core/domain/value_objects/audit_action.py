from __future__ import annotations

from enum import Enum


class AuditAction(str, Enum):
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"
    ORGANIZATION_CREATE = "organization.create"
    ORGANIZATION_UPDATE = "organization.update"
    ORGANIZATION_ACTIVATE = "organization.activate"
    ORGANIZATION_DEACTIVATE = "organization.deactivate"
    MEMBERSHIP_CREATE = "membership.create"
    MEMBERSHIP_ROLE_CHANGE = "membership.role_change"
    MEMBERSHIP_ACTIVATE = "membership.activate"
    MEMBERSHIP_DEACTIVATE = "membership.deactivate"
    INVITATION_CREATE = "invitation.create"
    INVITATION_REVOKE = "invitation.revoke"
    INVITATION_REISSUE = "invitation.reissue"
    INVITATION_ACCEPT = "invitation.accept"
    AUTHORIZATION_PERMISSION_DENIED = "authorization.permission_denied"
    AUTHENTICATION_LOGIN_SUCCEEDED = "authentication.login.succeeded"
    AUTHENTICATION_LOGIN_FAILED = "authentication.login.failed"
    AUTHENTICATION_REFRESH_SUCCEEDED = "authentication.refresh.succeeded"
    AUTHENTICATION_REFRESH_FAILED = "authentication.refresh.failed"
    AUTHENTICATION_LOGOUT_SUCCEEDED = "authentication.logout.succeeded"
    AUTHENTICATION_REFRESH_REUSE_DETECTED = "authentication.refresh.reused"
    AUTHENTICATION_SESSION_REVOKED = "authentication.session.revoked"

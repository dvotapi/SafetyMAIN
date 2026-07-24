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
    SAFETY_HAZARD_CREATED = "safety.hazard.created"
    SAFETY_HAZARD_UPDATED = "safety.hazard.updated"
    SAFETY_HAZARD_ACTIVATED = "safety.hazard.activated"
    SAFETY_HAZARD_ARCHIVED = "safety.hazard.archived"
    SAFETY_HAZARD_RESTORED = "safety.hazard.restored"
    SAFETY_RISK_CREATED = "safety.risk.created"
    SAFETY_RISK_UPDATED = "safety.risk.updated"
    SAFETY_RISK_APPROVED = "safety.risk.approved"
    SAFETY_RISK_SUPERSEDED = "safety.risk.superseded"
    SAFETY_RISK_ARCHIVED = "safety.risk.archived"
    SAFETY_RISK_CONTROL_CREATED = "safety.risk_control.created"
    SAFETY_RISK_CONTROL_UPDATED = "safety.risk_control.updated"
    SAFETY_RISK_CONTROL_OWNER_ASSIGNED = "safety.risk_control.owner_assigned"
    SAFETY_RISK_CONTROL_OWNER_CHANGED = "safety.risk_control.owner_changed"
    SAFETY_RISK_CONTROL_PLANNED = "safety.risk_control.planned"
    SAFETY_RISK_CONTROL_IMPLEMENTATION_STARTED = (
        "safety.risk_control.implementation_started"
    )
    SAFETY_RISK_CONTROL_PROGRESS_UPDATED = "safety.risk_control.progress_updated"
    SAFETY_RISK_CONTROL_EVIDENCE_ADDED = "safety.risk_control.evidence_added"
    SAFETY_RISK_CONTROL_IMPLEMENTED = "safety.risk_control.implemented"
    SAFETY_RISK_CONTROL_VERIFICATION_RECORDED = (
        "safety.risk_control.verification_recorded"
    )
    SAFETY_RISK_CONTROL_VERIFIED_EFFECTIVE = "safety.risk_control.verified_effective"
    SAFETY_RISK_CONTROL_VERIFIED_PARTIALLY_EFFECTIVE = (
        "safety.risk_control.verified_partially_effective"
    )
    SAFETY_RISK_CONTROL_VERIFIED_INEFFECTIVE = (
        "safety.risk_control.verified_ineffective"
    )
    SAFETY_RISK_CONTROL_REVIEW_SCHEDULED = "safety.risk_control.review_scheduled"
    SAFETY_RISK_CONTROL_REVIEW_COMPLETED = "safety.risk_control.review_completed"
    SAFETY_RISK_CONTROL_SUSPENDED = "safety.risk_control.suspended"
    SAFETY_RISK_CONTROL_RESUMED = "safety.risk_control.resumed"
    SAFETY_RISK_CONTROL_SUPERSEDED = "safety.risk_control.superseded"
    SAFETY_RISK_CONTROL_ARCHIVED = "safety.risk_control.archived"
    SAFETY_RISK_CONTROL_CANCELLED = "safety.risk_control.cancelled"
    SAFETY_RISK_CONTROL_MATERIALIZED = "safety.risk_control.materialized"
    SAFETY_RISK_CONTROL_CORRECTION_RECORDED = "safety.risk_control.correction_recorded"

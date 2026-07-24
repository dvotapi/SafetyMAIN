from __future__ import annotations

from enum import Enum


class AuditResourceType(str, Enum):
    USER = "USER"
    ORGANIZATION = "ORGANIZATION"
    MEMBERSHIP = "MEMBERSHIP"
    INVITATION = "INVITATION"
    AUDIT_EVENT = "AUDIT_EVENT"
    SESSION = "SESSION"
    HAZARD = "HAZARD"
    RISK = "RISK"
    RISK_CONTROL = "RISK_CONTROL"

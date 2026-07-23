from __future__ import annotations

from enum import Enum


class AuditResourceType(str, Enum):
    USER = "USER"
    ORGANIZATION = "ORGANIZATION"
    MEMBERSHIP = "MEMBERSHIP"
    INVITATION = "INVITATION"
    AUDIT_EVENT = "AUDIT_EVENT"

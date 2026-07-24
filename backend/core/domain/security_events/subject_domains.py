from __future__ import annotations

from enum import Enum


class SecurityEventSubjectDomain(str, Enum):
    """Resource or subsystem affected by a persisted auditable security event."""

    USER = "USER"
    IDENTITY = "IDENTITY"
    ORGANIZATION = "ORGANIZATION"
    MEMBERSHIP = "MEMBERSHIP"
    INVITATION = "INVITATION"
    SESSION = "SESSION"
    CREDENTIAL = "CREDENTIAL"
    API_KEY = "API_KEY"
    AUDIT_EVENT = "AUDIT_EVENT"
    SECURITY_SYSTEM = "SECURITY_SYSTEM"

from __future__ import annotations

from enum import Enum


class SecurityEventCategory(str, Enum):
    """Primary security nature of a persisted auditable security event."""

    ADMINISTRATIVE = "ADMINISTRATIVE"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    SECURITY_INFRASTRUCTURE = "SECURITY_INFRASTRUCTURE"

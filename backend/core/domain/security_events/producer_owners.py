from __future__ import annotations

from enum import Enum


class SecurityEventProducerOwner(str, Enum):
    """Architectural capability that owns the security decision for an event type."""

    ADMINISTRATIVE_AUDIT = "ADMINISTRATIVE_AUDIT"
    AUTHORIZATION = "AUTHORIZATION"
    AUTHENTICATION = "AUTHENTICATION"
    SECURITY_INFRASTRUCTURE = "SECURITY_INFRASTRUCTURE"

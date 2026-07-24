from __future__ import annotations

from enum import Enum


class SecurityEventSignificance(str, Enum):
    """Optional static registry-level significance; not persisted in AuditEvent."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

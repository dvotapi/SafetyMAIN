from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class AuditIntegrityHash(BaseModel):
    """Lowercase SHA-256 hexadecimal digest for audit integrity chaining."""

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _SHA256_HEX_PATTERN.fullmatch(normalized):
            raise ValueError(
                "Audit integrity hash must be a 64-character lowercase hexadecimal SHA-256 digest."
            )
        return normalized


class AuditIntegrityVersion(BaseModel):
    """Integrity algorithm/version identifier for audit event hashing."""

    model_config = ConfigDict(frozen=True)

    value: int

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Audit integrity version must be positive.")
        return value


CURRENT_AUDIT_INTEGRITY_VERSION = AuditIntegrityVersion(value=1)

# Reserved organization UUID for the platform (org-less) audit integrity chain.
PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID = UUID("00000000-0000-4000-8000-000000000001")

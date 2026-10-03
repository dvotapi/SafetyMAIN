from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.safety_ids import DocumentFileId

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class DocumentApplicability(BaseModel):
    """Loose applicability scope of a compliance document.

    Positions, work types, and departments are free text until the Employee
    read-model formalises their codes (P11-004/006); asset links are deferred.
    """

    model_config = ConfigDict(frozen=True)

    positions: tuple[str, ...] = ()
    work_types: tuple[str, ...] = ()
    departments: tuple[str, ...] = ()
    asset_ids: tuple[UUID, ...] = ()

    @field_validator("positions", "work_types", "departments")
    @classmethod
    def strip_entries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(entry.strip() for entry in value)
        if any(not entry for entry in normalized):
            raise ValueError("Applicability entries must not be empty.")
        return normalized


class DocumentFile(BaseModel):
    """Metadata of one uploaded file of a compliance document (ADR-0006)."""

    model_config = ConfigDict(frozen=True)

    id: DocumentFileId = Field(default_factory=lambda: DocumentFileId(value=uuid4()))
    bucket: str
    key: str
    size_bytes: int
    content_type: str
    sha256: str
    original_filename: str
    uploaded_at: datetime
    uploaded_by: UserId

    @field_validator("bucket", "key", "content_type", "original_filename")
    @classmethod
    def require_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("File metadata fields must not be empty.")
        return normalized

    @field_validator("size_bytes")
    @classmethod
    def require_positive_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError("File size must be positive.")
        return value

    @field_validator("sha256")
    @classmethod
    def require_sha256_hex(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _SHA256_HEX.fullmatch(normalized):
            raise ValueError("SHA-256 must be 64 hexadecimal characters.")
        return normalized

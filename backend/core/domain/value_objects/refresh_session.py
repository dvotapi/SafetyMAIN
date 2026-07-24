from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class RefreshSessionId(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: UUID

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, UUID | str):
            return {"value": data}
        return data


class RefreshTokenFamilyId(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: UUID

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, UUID | str):
            return {"value": data}
        return data


class RefreshTokenIdHash(BaseModel):
    """SHA-256 hex digest of a refresh-token jti."""

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def normalize_hash(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64:
            raise ValueError("Refresh token ID hash must be 64 hexadecimal characters.")
        if any(character not in "0123456789abcdef" for character in normalized):
            raise ValueError("Refresh token ID hash must be hexadecimal.")
        return normalized


class RefreshSessionRevocationReason(str, Enum):
    LOGOUT = "logout"
    TOKEN_REUSE_DETECTED = "token_reuse_detected"
    USER_DEACTIVATED = "user_deactivated"
    ADMINISTRATIVE_REVOCATION = "administrative_revocation"
    SESSION_EXPIRED = "session_expired"
    SECURITY_RESPONSE = "security_response"

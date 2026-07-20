from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import UserId


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class User(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: UserId = Field(frozen=True)
    display_name: str
    email: str
    status: UserStatus
    external_subject: str | None = Field(default=None, frozen=True)
    created_at: datetime = Field(frozen=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if not normalized_value:
            raise ValueError("User email must not be empty.")

        return normalized_value

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("User display name must not be empty.")

        return normalized_value

    def is_active(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def can_authenticate(self) -> bool:
        return self.status is UserStatus.ACTIVE

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import OrganizationId

ORGANIZATION_NAME_MAX_LENGTH = 255


class OrganizationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"


def normalized_organization_name_key(name: str) -> str:
    return name.strip().casefold()


class Organization(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: OrganizationId = Field(frozen=True)
    name: str
    status: OrganizationStatus
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Organization name must not be empty.")

        if len(normalized_value) > ORGANIZATION_NAME_MAX_LENGTH:
            raise ValueError(
                f"Organization name must not exceed {ORGANIZATION_NAME_MAX_LENGTH} characters."
            )

        return normalized_value

    def is_active(self) -> bool:
        return self.status is OrganizationStatus.ACTIVE

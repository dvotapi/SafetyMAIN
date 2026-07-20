from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.domain.value_objects import OrganizationId


class Organization(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: OrganizationId = Field(frozen=True)
    name: str
    created_at: datetime = Field(frozen=True)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Organization name must not be empty.")

        return normalized_value

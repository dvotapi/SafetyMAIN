from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SystemRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    AUDITOR = "auditor"


class Role(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, SystemRole):
            return {"value": data.value}
        if isinstance(data, str):
            return {"value": data}
        return data

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if not normalized_value:
            raise ValueError("Role must not be empty.")

        return normalized_value

    @classmethod
    def admin(cls) -> Role:
        return cls(value=SystemRole.ADMIN.value)

    @classmethod
    def member(cls) -> Role:
        return cls(value=SystemRole.MEMBER.value)

    @classmethod
    def auditor(cls) -> Role:
        return cls(value=SystemRole.AUDITOR.value)

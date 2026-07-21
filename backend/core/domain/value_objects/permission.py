from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SystemPermission(str, Enum):
    KNOWLEDGE_OBJECT_READ = "knowledge_object:read"
    KNOWLEDGE_OBJECT_WRITE = "knowledge_object:write"
    RELATION_MANAGE = "relation:manage"
    MEMBERSHIP_MANAGE = "membership:manage"
    ORGANIZATION_ADMIN = "organization:admin"
    USER_READ = "user:read"
    USER_WRITE = "user:write"


class Permission(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, SystemPermission):
            return {"value": data.value}
        if isinstance(data, str):
            return {"value": data}
        return data

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if not normalized_value:
            raise ValueError("Permission must not be empty.")

        return normalized_value

    @classmethod
    def from_system_permission(cls, permission: SystemPermission) -> Permission:
        return cls(value=permission.value)

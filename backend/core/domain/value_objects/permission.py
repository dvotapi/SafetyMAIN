from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class SystemPermission(str, Enum):
    KNOWLEDGE_OBJECT_READ = "knowledge_object:read"
    KNOWLEDGE_OBJECT_WRITE = "knowledge_object:write"
    RELATION_MANAGE = "relation:manage"
    MEMBERSHIP_MANAGE = "membership:manage"
    MEMBERSHIP_READ = "membership:read"
    MEMBERSHIP_WRITE = "membership:write"
    ORGANIZATION_ADMIN = "organization:admin"
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_WRITE = "organization:write"
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    INVITATION_READ = "invitation:read"
    INVITATION_WRITE = "invitation:write"
    AUDIT_READ = "audit:read"
    HAZARD_READ = "hazard:read"
    HAZARD_CREATE = "hazard:create"
    HAZARD_UPDATE = "hazard:update"
    HAZARD_ACTIVATE = "hazard:activate"
    HAZARD_ARCHIVE = "hazard:archive"
    HAZARD_RESTORE = "hazard:restore"
    RISK_READ = "risk:read"
    RISK_CREATE = "risk:create"
    RISK_UPDATE = "risk:update"
    RISK_REVIEW = "risk:review"
    RISK_APPROVE = "risk:approve"
    RISK_ARCHIVE = "risk:archive"
    RISK_CONTROL_READ = "risk_control:read"
    RISK_CONTROL_CREATE = "risk_control:create"
    RISK_CONTROL_UPDATE = "risk_control:update"
    RISK_CONTROL_ASSIGN = "risk_control:assign"
    RISK_CONTROL_IMPLEMENT = "risk_control:implement"
    RISK_CONTROL_VERIFY = "risk_control:verify"
    RISK_CONTROL_REVIEW = "risk_control:review"
    RISK_CONTROL_SUSPEND = "risk_control:suspend"
    RISK_CONTROL_SUPERSEDE = "risk_control:supersede"
    RISK_CONTROL_ARCHIVE = "risk_control:archive"
    RISK_CONTROL_CANCEL = "risk_control:cancel"
    RISK_CONTROL_MATERIALIZE = "risk_control:materialize"


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

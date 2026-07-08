from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class KnowledgeObjectType(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            return {"value": data}
        return data

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if not normalized_value:
            raise ValueError("Knowledge Object type must not be empty.")

        return normalized_value

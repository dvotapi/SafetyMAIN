from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KnowledgeObjectVersion(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: int = Field(ge=1)

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, int):
            return {"value": data}
        return data

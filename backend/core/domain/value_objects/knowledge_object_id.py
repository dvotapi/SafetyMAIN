from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class KnowledgeObjectId(BaseModel):
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

from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.entities.knowledge_object import KnowledgeObject


class KnowledgeObjectSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: Sequence[KnowledgeObject] = Field(default_factory=tuple)
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)

    @classmethod
    def create(
        cls,
        *,
        items: Sequence[KnowledgeObject],
        total: int,
        limit: int,
        offset: int,
    ) -> KnowledgeObjectSearchResult:
        return cls(
            items=tuple(items),
            total=total,
            limit=limit,
            offset=offset,
        )

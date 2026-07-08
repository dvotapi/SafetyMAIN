from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol


EntityId = str
EntityType = str
EntityVersion = int


class EntityContract(Protocol):
    """Base contract for Core entities."""

    id: EntityId
    type: EntityType
    version: EntityVersion
    created_at: datetime
    updated_at: datetime
    metadata: Mapping[str, Any]

from __future__ import annotations

from typing import Literal

from backend.core.domain.events.base_event import BaseDomainEvent


class KnowledgeObjectRelationCreated(BaseDomainEvent):
    event_type: Literal["knowledge_object_relation.created"] = (
        "knowledge_object_relation.created"
    )

from __future__ import annotations

from typing import Literal

from backend.core.domain.events.base_event import BaseDomainEvent


class KnowledgeObjectCreated(BaseDomainEvent):
    event_type: Literal["knowledge_object.created"] = "knowledge_object.created"

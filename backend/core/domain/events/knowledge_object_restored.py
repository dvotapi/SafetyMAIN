from __future__ import annotations

from typing import Literal

from backend.core.domain.events.base_event import BaseDomainEvent


class KnowledgeObjectRestored(BaseDomainEvent):
    event_type: Literal["knowledge_object.restored"] = "knowledge_object.restored"

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol


EventId = str
EventType = str
EventSource = str


class EventContract(Protocol):
    """Contract for Core domain events."""

    id: EventId
    type: EventType
    source: EventSource
    occurred_at: datetime
    payload: Mapping[str, Any]


class EventHandlerContract(Protocol):
    """Contract for event handlers."""

    def handle(self, event: EventContract) -> None:
        ...


class EventPublisherContract(Protocol):
    """Contract for event publishers."""

    def publish(self, event: EventContract) -> None:
        ...

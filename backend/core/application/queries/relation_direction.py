from __future__ import annotations

from enum import Enum


class RelationDirection(str, Enum):
    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH = "BOTH"

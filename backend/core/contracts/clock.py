from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockContract(Protocol):
    def now(self) -> datetime:
        ...

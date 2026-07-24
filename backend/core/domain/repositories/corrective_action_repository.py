from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.corrective_action import CorrectiveAction
from backend.core.domain.value_objects.safety_ids import CorrectiveActionId


class CorrectiveActionRepositoryContract(Protocol):
    def add(self, action: CorrectiveAction) -> None:
        ...

    def get(self, action_id: CorrectiveActionId) -> CorrectiveAction:
        ...

    def save(self, action: CorrectiveAction) -> None:
        ...

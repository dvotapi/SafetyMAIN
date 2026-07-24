from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.inspection import Inspection
from backend.core.domain.value_objects.safety_ids import InspectionId


class InspectionRepositoryContract(Protocol):
    def add(self, inspection: Inspection) -> None:
        ...

    def get(self, inspection_id: InspectionId) -> Inspection:
        ...

    def save(self, inspection: Inspection) -> None:
        ...

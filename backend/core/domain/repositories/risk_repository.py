from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.risk import Risk
from backend.core.domain.value_objects.safety_ids import HazardId, RiskId


class RiskRepositoryContract(Protocol):
    def add(self, risk: Risk) -> None:
        ...

    def get(self, risk_id: RiskId) -> Risk:
        ...

    def save(self, risk: Risk) -> None:
        ...

    def list_for_hazard(self, hazard_id: HazardId) -> tuple[Risk, ...]:
        ...

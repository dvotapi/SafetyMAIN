from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.training_permit_emergency_asset import (
    Asset,
    EmergencyPlan,
    Permit,
    Training,
)
from backend.core.domain.value_objects.safety_ids import (
    AssetId,
    EmergencyPlanId,
    PermitId,
    TrainingId,
)


class TrainingRepositoryContract(Protocol):
    def add(self, training: Training) -> None:
        ...

    def get(self, training_id: TrainingId) -> Training:
        ...

    def save(self, training: Training) -> None:
        ...


class PermitRepositoryContract(Protocol):
    def add(self, permit: Permit) -> None:
        ...

    def get(self, permit_id: PermitId) -> Permit:
        ...

    def save(self, permit: Permit) -> None:
        ...


class EmergencyPlanRepositoryContract(Protocol):
    def add(self, plan: EmergencyPlan) -> None:
        ...

    def get(self, plan_id: EmergencyPlanId) -> EmergencyPlan:
        ...

    def save(self, plan: EmergencyPlan) -> None:
        ...


class AssetRepositoryContract(Protocol):
    def add(self, asset: Asset) -> None:
        ...

    def get(self, asset_id: AssetId) -> Asset:
        ...

    def save(self, asset: Asset) -> None:
        ...

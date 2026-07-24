from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.services.safety_lifecycle import transition
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    AssetStatus,
    EmergencyPlanStatus,
    PermitStatus,
    TrainingStatus,
)
from backend.core.domain.value_objects.safety_ids import (
    AssetId,
    EmergencyPlanId,
    PermitId,
    TrainingId,
)

_TRAINING_TRANSITIONS: dict[str, frozenset[str]] = {
    TrainingStatus.PLANNED.value: frozenset(
        {TrainingStatus.IN_PROGRESS.value, TrainingStatus.ARCHIVED.value}
    ),
    TrainingStatus.IN_PROGRESS.value: frozenset(
        {TrainingStatus.COMPLETED.value, TrainingStatus.ARCHIVED.value}
    ),
    TrainingStatus.COMPLETED.value: frozenset(
        {TrainingStatus.EXPIRED.value, TrainingStatus.ARCHIVED.value}
    ),
    TrainingStatus.EXPIRED.value: frozenset({TrainingStatus.ARCHIVED.value}),
    TrainingStatus.ARCHIVED.value: frozenset(),
}

_PERMIT_TRANSITIONS: dict[str, frozenset[str]] = {
    PermitStatus.DRAFT.value: frozenset(
        {PermitStatus.ISSUED.value, PermitStatus.ARCHIVED.value}
    ),
    PermitStatus.ISSUED.value: frozenset(
        {
            PermitStatus.CLOSED.value,
            PermitStatus.SUSPENDED.value,
            PermitStatus.ARCHIVED.value,
        }
    ),
    PermitStatus.SUSPENDED.value: frozenset(
        {PermitStatus.ISSUED.value, PermitStatus.CLOSED.value}
    ),
    PermitStatus.CLOSED.value: frozenset({PermitStatus.ARCHIVED.value}),
    PermitStatus.ARCHIVED.value: frozenset(),
}

_EMERGENCY_TRANSITIONS: dict[str, frozenset[str]] = {
    EmergencyPlanStatus.DRAFT.value: frozenset(
        {EmergencyPlanStatus.ACTIVE.value, EmergencyPlanStatus.ARCHIVED.value}
    ),
    EmergencyPlanStatus.ACTIVE.value: frozenset(
        {
            EmergencyPlanStatus.UNDER_REVIEW.value,
            EmergencyPlanStatus.ARCHIVED.value,
        }
    ),
    EmergencyPlanStatus.UNDER_REVIEW.value: frozenset(
        {EmergencyPlanStatus.ACTIVE.value, EmergencyPlanStatus.ARCHIVED.value}
    ),
    EmergencyPlanStatus.ARCHIVED.value: frozenset(),
}

_ASSET_TRANSITIONS: dict[str, frozenset[str]] = {
    AssetStatus.ACTIVE.value: frozenset(
        {AssetStatus.INACTIVE.value, AssetStatus.DECOMMISSIONED.value}
    ),
    AssetStatus.INACTIVE.value: frozenset(
        {AssetStatus.ACTIVE.value, AssetStatus.DECOMMISSIONED.value}
    ),
    AssetStatus.DECOMMISSIONED.value: frozenset(),
}


class Training(BaseModel):
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: TrainingId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: TrainingStatus = TrainingStatus.PLANNED
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    completed_at: datetime | None = None

    def start(self, *, at: datetime) -> Training:
        transition(
            aggregate="training",
            current=self.status.value,
            target=TrainingStatus.IN_PROGRESS.value,
            allowed=_TRAINING_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": TrainingStatus.IN_PROGRESS, "updated_at": at}
        )

    def complete(self, *, at: datetime) -> Training:
        transition(
            aggregate="training",
            current=self.status.value,
            target=TrainingStatus.COMPLETED.value,
            allowed=_TRAINING_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": TrainingStatus.COMPLETED,
                "completed_at": at,
                "updated_at": at,
            }
        )


class Permit(BaseModel):
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: PermitId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: PermitStatus = PermitStatus.DRAFT
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    def issue(self, *, valid_from: datetime, valid_to: datetime, at: datetime) -> Permit:
        if valid_to <= valid_from:
            raise ValueError("Permit validity window requires valid_to > valid_from.")
        transition(
            aggregate="permit",
            current=self.status.value,
            target=PermitStatus.ISSUED.value,
            allowed=_PERMIT_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": PermitStatus.ISSUED,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "updated_at": at,
            }
        )

    def close(self, *, at: datetime) -> Permit:
        transition(
            aggregate="permit",
            current=self.status.value,
            target=PermitStatus.CLOSED.value,
            allowed=_PERMIT_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": PermitStatus.CLOSED, "updated_at": at}
        )


class EmergencyPlan(BaseModel):
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: EmergencyPlanId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: EmergencyPlanStatus = EmergencyPlanStatus.DRAFT
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    def activate(self, *, at: datetime) -> EmergencyPlan:
        transition(
            aggregate="emergency_plan",
            current=self.status.value,
            target=EmergencyPlanStatus.ACTIVE.value,
            allowed=_EMERGENCY_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": EmergencyPlanStatus.ACTIVE, "updated_at": at}
        )


class Asset(BaseModel):
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: AssetId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    name: str
    status: AssetStatus = AssetStatus.ACTIVE
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    def decommission(self, *, at: datetime) -> Asset:
        transition(
            aggregate="asset",
            current=self.status.value,
            target=AssetStatus.DECOMMISSIONED.value,
            allowed=_ASSET_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": AssetStatus.DECOMMISSIONED, "updated_at": at}
        )

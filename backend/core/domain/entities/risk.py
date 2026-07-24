from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.core.domain.services.safety_lifecycle import transition
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    ControlType,
    Probability,
    RiskLevel,
    RiskStatus,
    Severity,
)
from backend.core.domain.value_objects.safety_ids import ControlId, HazardId, RiskId

_RISK_TRANSITIONS: dict[str, frozenset[str]] = {
    RiskStatus.DRAFT.value: frozenset(
        {RiskStatus.ASSESSED.value, RiskStatus.ARCHIVED.value}
    ),
    RiskStatus.ASSESSED.value: frozenset(
        {RiskStatus.ACCEPTED.value, RiskStatus.ARCHIVED.value}
    ),
    RiskStatus.ACCEPTED.value: frozenset(
        {RiskStatus.MONITORING.value, RiskStatus.ARCHIVED.value}
    ),
    RiskStatus.MONITORING.value: frozenset(
        {RiskStatus.ASSESSED.value, RiskStatus.ARCHIVED.value}
    ),
    RiskStatus.ARCHIVED.value: frozenset(),
}


class Control(BaseModel):
    """Control measure owned by a Risk aggregate."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: ControlId = Field(frozen=True)
    title: str
    control_type: ControlType
    implemented: bool = False


class Risk(BaseModel):
    """Aggregate root for a hazard risk assessment outcome."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: RiskId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    hazard_id: HazardId = Field(frozen=True)
    status: RiskStatus = RiskStatus.DRAFT
    probability: Probability | None = None
    severity: Severity | None = None
    inherent_level: RiskLevel | None = None
    residual_level: RiskLevel | None = None
    controls: tuple[Control, ...] = ()
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    @model_validator(mode="after")
    def validate_controls_unique(self) -> Risk:
        ids = [control.id.value for control in self.controls]
        if len(ids) != len(set(ids)):
            raise ValueError("Control identifiers must be unique within a Risk.")
        return self

    def assess(
        self,
        *,
        probability: Probability,
        severity: Severity,
        inherent_level: RiskLevel,
        residual_level: RiskLevel | None = None,
        at: datetime,
    ) -> Risk:
        transition(
            aggregate="risk",
            current=self.status.value,
            target=RiskStatus.ASSESSED.value,
            allowed=_RISK_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": RiskStatus.ASSESSED,
                "probability": probability,
                "severity": severity,
                "inherent_level": inherent_level,
                "residual_level": residual_level or inherent_level,
                "updated_at": at,
            }
        )

    def accept(self, *, at: datetime) -> Risk:
        transition(
            aggregate="risk",
            current=self.status.value,
            target=RiskStatus.ACCEPTED.value,
            allowed=_RISK_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": RiskStatus.ACCEPTED, "updated_at": at}
        )

    def with_control(self, control: Control, *, at: datetime) -> Risk:
        return self.model_copy(
            update={
                "controls": (*self.controls, control),
                "updated_at": at,
            }
        )

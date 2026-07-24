from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class _UuidIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: UUID

    @model_validator(mode="before")
    @classmethod
    def validate_value(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, UUID | str):
            return {"value": data}
        return data


class HazardId(_UuidIdentity):
    pass


class RiskId(_UuidIdentity):
    pass


class RiskAssessmentId(_UuidIdentity):
    pass


class InspectionId(_UuidIdentity):
    pass


class IncidentId(_UuidIdentity):
    pass


class TrainingId(_UuidIdentity):
    pass


class PermitId(_UuidIdentity):
    pass


class EmergencyPlanId(_UuidIdentity):
    pass


class AssetId(_UuidIdentity):
    pass


class FindingId(_UuidIdentity):
    pass


class CorrectiveActionId(_UuidIdentity):
    pass


class ControlId(_UuidIdentity):
    pass


class RiskControlId(_UuidIdentity):
    pass

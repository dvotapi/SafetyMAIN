from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.services.safety_lifecycle import transition
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import (
    FindingSeverity,
    InspectionStatus,
)
from backend.core.domain.value_objects.safety_ids import FindingId, InspectionId

_INSPECTION_TRANSITIONS: dict[str, frozenset[str]] = {
    InspectionStatus.PLANNED.value: frozenset({InspectionStatus.IN_PROGRESS.value}),
    InspectionStatus.IN_PROGRESS.value: frozenset({InspectionStatus.COMPLETED.value}),
    InspectionStatus.COMPLETED.value: frozenset({InspectionStatus.ARCHIVED.value}),
    InspectionStatus.ARCHIVED.value: frozenset(),
}


class Finding(BaseModel):
    """Finding owned by an Inspection aggregate."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: FindingId = Field(frozen=True)
    summary: str
    severity: FindingSeverity
    created_at: datetime = Field(frozen=True)


class Inspection(BaseModel):
    """Aggregate root for workplace or asset inspections."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: InspectionId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: InspectionStatus = InspectionStatus.PLANNED
    findings: tuple[Finding, ...] = ()
    created_at: datetime = Field(frozen=True)
    updated_at: datetime
    completed_at: datetime | None = None

    def start(self, *, at: datetime) -> Inspection:
        transition(
            aggregate="inspection",
            current=self.status.value,
            target=InspectionStatus.IN_PROGRESS.value,
            allowed=_INSPECTION_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": InspectionStatus.IN_PROGRESS, "updated_at": at}
        )

    def add_finding(self, finding: Finding, *, at: datetime) -> Inspection:
        if self.status is not InspectionStatus.IN_PROGRESS:
            raise ValueError("Findings may only be added while inspection is in progress.")
        return self.model_copy(
            update={"findings": (*self.findings, finding), "updated_at": at}
        )

    def complete(self, *, at: datetime) -> Inspection:
        transition(
            aggregate="inspection",
            current=self.status.value,
            target=InspectionStatus.COMPLETED.value,
            allowed=_INSPECTION_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": InspectionStatus.COMPLETED,
                "completed_at": at,
                "updated_at": at,
            }
        )

    def archive(self, *, at: datetime) -> Inspection:
        transition(
            aggregate="inspection",
            current=self.status.value,
            target=InspectionStatus.ARCHIVED.value,
            allowed=_INSPECTION_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": InspectionStatus.ARCHIVED, "updated_at": at}
        )

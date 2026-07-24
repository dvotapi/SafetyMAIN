from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.services.safety_lifecycle import transition
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.safety_enums import IncidentStatus
from backend.core.domain.value_objects.safety_ids import IncidentId

_INCIDENT_TRANSITIONS: dict[str, frozenset[str]] = {
    IncidentStatus.REPORTED.value: frozenset(
        {IncidentStatus.UNDER_INVESTIGATION.value, IncidentStatus.ARCHIVED.value}
    ),
    IncidentStatus.UNDER_INVESTIGATION.value: frozenset(
        {IncidentStatus.ACTIONS_PENDING.value, IncidentStatus.CLOSED.value}
    ),
    IncidentStatus.ACTIONS_PENDING.value: frozenset({IncidentStatus.CLOSED.value}),
    IncidentStatus.CLOSED.value: frozenset({IncidentStatus.ARCHIVED.value}),
    IncidentStatus.ARCHIVED.value: frozenset(),
}


class Incident(BaseModel):
    """Aggregate root for incidents and near misses."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: IncidentId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: IncidentStatus = IncidentStatus.REPORTED
    is_near_miss: bool = False
    occurred_at: datetime
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    def begin_investigation(self, *, at: datetime) -> Incident:
        transition(
            aggregate="incident",
            current=self.status.value,
            target=IncidentStatus.UNDER_INVESTIGATION.value,
            allowed=_INCIDENT_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": IncidentStatus.UNDER_INVESTIGATION,
                "updated_at": at,
            }
        )

    def mark_actions_pending(self, *, at: datetime) -> Incident:
        transition(
            aggregate="incident",
            current=self.status.value,
            target=IncidentStatus.ACTIONS_PENDING.value,
            allowed=_INCIDENT_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": IncidentStatus.ACTIONS_PENDING, "updated_at": at}
        )

    def close(self, *, at: datetime) -> Incident:
        transition(
            aggregate="incident",
            current=self.status.value,
            target=IncidentStatus.CLOSED.value,
            allowed=_INCIDENT_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": IncidentStatus.CLOSED, "updated_at": at}
        )

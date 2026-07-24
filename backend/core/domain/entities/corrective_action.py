from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.core.domain.services.safety_lifecycle import transition
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.safety_enums import CorrectiveActionStatus
from backend.core.domain.value_objects.safety_ids import CorrectiveActionId

_CA_TRANSITIONS: dict[str, frozenset[str]] = {
    CorrectiveActionStatus.OPEN.value: frozenset({CorrectiveActionStatus.ASSIGNED.value}),
    CorrectiveActionStatus.ASSIGNED.value: frozenset(
        {CorrectiveActionStatus.IN_PROGRESS.value}
    ),
    CorrectiveActionStatus.IN_PROGRESS.value: frozenset(
        {CorrectiveActionStatus.COMPLETED.value}
    ),
    CorrectiveActionStatus.COMPLETED.value: frozenset(
        {CorrectiveActionStatus.VERIFIED.value}
    ),
    CorrectiveActionStatus.VERIFIED.value: frozenset(
        {CorrectiveActionStatus.CLOSED.value}
    ),
    CorrectiveActionStatus.CLOSED.value: frozenset(),
}


class CorrectiveAction(BaseModel):
    """Aggregate root for corrective (and future preventive) actions."""

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    id: CorrectiveActionId = Field(frozen=True)
    organization_id: OrganizationId = Field(frozen=True)
    title: str
    status: CorrectiveActionStatus = CorrectiveActionStatus.OPEN
    assignee_user_id: UserId | None = None
    origin_reference: str | None = None
    created_at: datetime = Field(frozen=True)
    updated_at: datetime

    def assign(self, assignee_user_id: UserId, *, at: datetime) -> CorrectiveAction:
        transition(
            aggregate="corrective_action",
            current=self.status.value,
            target=CorrectiveActionStatus.ASSIGNED.value,
            allowed=_CA_TRANSITIONS,
        )
        return self.model_copy(
            update={
                "status": CorrectiveActionStatus.ASSIGNED,
                "assignee_user_id": assignee_user_id,
                "updated_at": at,
            }
        )

    def start(self, *, at: datetime) -> CorrectiveAction:
        transition(
            aggregate="corrective_action",
            current=self.status.value,
            target=CorrectiveActionStatus.IN_PROGRESS.value,
            allowed=_CA_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": CorrectiveActionStatus.IN_PROGRESS, "updated_at": at}
        )

    def complete(self, *, at: datetime) -> CorrectiveAction:
        transition(
            aggregate="corrective_action",
            current=self.status.value,
            target=CorrectiveActionStatus.COMPLETED.value,
            allowed=_CA_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": CorrectiveActionStatus.COMPLETED, "updated_at": at}
        )

    def verify(self, *, at: datetime) -> CorrectiveAction:
        transition(
            aggregate="corrective_action",
            current=self.status.value,
            target=CorrectiveActionStatus.VERIFIED.value,
            allowed=_CA_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": CorrectiveActionStatus.VERIFIED, "updated_at": at}
        )

    def close(self, *, at: datetime) -> CorrectiveAction:
        transition(
            aggregate="corrective_action",
            current=self.status.value,
            target=CorrectiveActionStatus.CLOSED.value,
            allowed=_CA_TRANSITIONS,
        )
        return self.model_copy(
            update={"status": CorrectiveActionStatus.CLOSED, "updated_at": at}
        )

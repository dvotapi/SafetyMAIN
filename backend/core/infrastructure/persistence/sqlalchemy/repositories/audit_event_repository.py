from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound
from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.audit_event_mapper import (
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditEventModel,
)


class SQLAlchemyAuditEventRepository(AuditEventRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: AuditEvent) -> None:
        self._session.add(to_model(event))

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        model = self._session.get(AuditEventModel, audit_event_id.value)
        if model is None:
            raise AuditEventNotFound(audit_event_id)
        return to_domain(model)

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        scope_id = criteria.scope_organization_id.value
        filters: list[object] = [
            or_(
                AuditEventModel.authorization_organization_id == scope_id,
                AuditEventModel.target_organization_id == scope_id,
            )
        ]
        if criteria.action is not None:
            filters.append(AuditEventModel.action == criteria.action.value)
        if criteria.resource_type is not None:
            filters.append(AuditEventModel.resource_type == criteria.resource_type.value)
        if criteria.resource_id is not None:
            filters.append(AuditEventModel.resource_id == criteria.resource_id)
        if criteria.actor_user_id is not None:
            filters.append(AuditEventModel.actor_user_id == criteria.actor_user_id.value)
        if criteria.outcome is not None:
            filters.append(AuditEventModel.outcome == criteria.outcome.value)
        if criteria.target_organization_id is not None:
            filters.append(
                AuditEventModel.target_organization_id
                == criteria.target_organization_id.value
            )
        if criteria.occurred_from is not None:
            filters.append(AuditEventModel.occurred_at >= criteria.occurred_from)
        if criteria.occurred_to is not None:
            filters.append(AuditEventModel.occurred_at <= criteria.occurred_to)

        models = self._session.scalars(select(AuditEventModel).where(*filters)).all()
        events = [to_domain(model) for model in models]
        events.sort(key=lambda event: event.id.value)
        events.sort(key=lambda event: event.occurred_at, reverse=not criteria.sort_ascending)
        total = len(events)
        page = events[criteria.offset : criteria.offset + criteria.limit]

        return AuditEventListResult(
            items=tuple(page),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

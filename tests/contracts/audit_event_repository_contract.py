from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound
from backend.core.domain.repositories.audit_event_repository import AuditEventRepositoryContract
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import AuditEventListCriteria
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def build_audit_event(
    *,
    scope_organization_id: OrganizationId,
    action: AuditAction = AuditAction.USER_CREATE,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    actor_user_id: UserId | None = None,
    target_organization_id: OrganizationId | None = None,
    resource_id: UUID | None = None,
    occurred_at: datetime | None = None,
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    return AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=actor_user_id or UserId(value=uuid4()),
        authorization_organization_id=scope_organization_id,
        target_organization_id=target_organization_id,
        action=action,
        resource_type=AuditResourceType.USER,
        resource_id=resource_id or uuid4(),
        outcome=outcome,
        failure_code="duplicate_user_email" if outcome is AuditOutcome.FAILURE else None,
        metadata=metadata or {},
        occurred_at=occurred_at or datetime.now(UTC),
    )


class AuditEventRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> AuditEventRepositoryContract:
        raise NotImplementedError

    def test_append_and_get(self, repository: AuditEventRepositoryContract) -> None:
        scope = OrganizationId(value=uuid4())
        event = build_audit_event(scope_organization_id=scope)

        repository.add(event)

        assert repository.get(event.id) == event

    def test_get_missing_event_raises(self, repository: AuditEventRepositoryContract) -> None:
        missing_id = AuditEventId(value=uuid4())

        with pytest.raises(AuditEventNotFound):
            repository.get(missing_id)

    def test_list_scopes_by_authorization_or_target_organization(
        self,
        repository: AuditEventRepositoryContract,
    ) -> None:
        scope = OrganizationId(value=uuid4())
        other = OrganizationId(value=uuid4())
        in_scope = build_audit_event(scope_organization_id=scope)
        target_scoped = build_audit_event(
            scope_organization_id=other,
            target_organization_id=scope,
        )
        out_of_scope = build_audit_event(scope_organization_id=other)

        repository.add(in_scope)
        repository.add(target_scoped)
        repository.add(out_of_scope)

        result = repository.list_events(
            AuditEventListCriteria(scope_organization_id=scope, offset=0, limit=10)
        )

        assert result.total == 2
        assert {item.id for item in result.items} == {in_scope.id, target_scoped.id}

    def test_list_filters_by_action_outcome_and_actor(
        self,
        repository: AuditEventRepositoryContract,
    ) -> None:
        scope = OrganizationId(value=uuid4())
        actor = UserId(value=uuid4())
        matching = build_audit_event(
            scope_organization_id=scope,
            actor_user_id=actor,
            action=AuditAction.USER_UPDATE,
            outcome=AuditOutcome.FAILURE,
        )
        repository.add(matching)
        repository.add(
            build_audit_event(
                scope_organization_id=scope,
                action=AuditAction.USER_CREATE,
                outcome=AuditOutcome.SUCCESS,
            )
        )

        result = repository.list_events(
            AuditEventListCriteria(
                scope_organization_id=scope,
                offset=0,
                limit=10,
                action=AuditAction.USER_UPDATE,
                outcome=AuditOutcome.FAILURE,
                actor_user_id=actor,
            )
        )

        assert result.total == 1
        assert result.items[0].id == matching.id

    def test_list_supports_timestamp_range_and_pagination(
        self,
        repository: AuditEventRepositoryContract,
    ) -> None:
        scope = OrganizationId(value=uuid4())
        base = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
        events = [
            build_audit_event(
                scope_organization_id=scope,
                occurred_at=base + timedelta(minutes=index),
            )
            for index in range(3)
        ]
        for event in events:
            repository.add(event)

        result = repository.list_events(
            AuditEventListCriteria(
                scope_organization_id=scope,
                offset=1,
                limit=1,
                occurred_from=base,
                occurred_to=base + timedelta(minutes=2),
                sort_ascending=False,
            )
        )

        assert result.total == 3
        assert len(result.items) == 1
        assert result.items[0].id == events[1].id

    def test_list_persists_metadata(self, repository: AuditEventRepositoryContract) -> None:
        scope = OrganizationId(value=uuid4())
        event = build_audit_event(
            scope_organization_id=scope,
            metadata={"changed_fields": ["display_name"]},
        )

        repository.add(event)

        listed = repository.list_events(
            AuditEventListCriteria(scope_organization_id=scope, offset=0, limit=10)
        )

        assert listed.items[0].metadata == {"changed_fields": ["display_name"]}

    def test_repository_has_no_update_or_delete_methods(
        self,
        repository: AuditEventRepositoryContract,
    ) -> None:
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")
        assert not hasattr(repository, "activate")
        assert not hasattr(repository, "deactivate")

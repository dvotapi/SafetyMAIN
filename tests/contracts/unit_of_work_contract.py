from __future__ import annotations

from collections.abc import Callable
import pytest

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.exceptions import (
    KnowledgeObjectNotFound,
    KnowledgeObjectRelationNotFound,
)
from tests.contracts.knowledge_object_relation_repository_contract import create_relation
from tests.contracts.knowledge_object_repository_contract import create_knowledge_object


class UnitOfWorkContractSuite:
    @pytest.fixture()
    def unit_of_work_factory(self) -> Callable[[], UnitOfWorkContract]:
        raise NotImplementedError

    def test_repositories_available_inside_context(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        with unit_of_work_factory() as unit_of_work:
            assert unit_of_work.knowledge_objects is not None
            assert unit_of_work.relations is not None
            assert unit_of_work.users is not None
            assert unit_of_work.organizations is not None
            assert unit_of_work.memberships is not None

    def test_commit_preserves_changes(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        source = create_knowledge_object()
        target = create_knowledge_object(organization_id=source.header.organization_id)
        relation = create_relation(source=source, target=target)

        with unit_of_work_factory() as unit_of_work:
            unit_of_work.knowledge_objects.add(source)
            unit_of_work.knowledge_objects.add(target)
            unit_of_work.relations.add(relation)
            unit_of_work.commit()

        with unit_of_work_factory() as unit_of_work:
            assert unit_of_work.knowledge_objects.get(source.header.id) == source
            assert unit_of_work.knowledge_objects.get(target.header.id) == target
            assert unit_of_work.relations.get(relation.relation_id) == relation

    def test_exit_without_commit_rolls_back(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        knowledge_object = create_knowledge_object()

        with unit_of_work_factory() as unit_of_work:
            unit_of_work.knowledge_objects.add(knowledge_object)

        with unit_of_work_factory() as unit_of_work:
            with pytest.raises(KnowledgeObjectNotFound):
                unit_of_work.knowledge_objects.get(knowledge_object.header.id)

    def test_exception_rolls_back_and_is_not_suppressed(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        knowledge_object = create_knowledge_object()

        with pytest.raises(RuntimeError):
            with unit_of_work_factory() as unit_of_work:
                unit_of_work.knowledge_objects.add(knowledge_object)
                raise RuntimeError("rollback")

        with unit_of_work_factory() as unit_of_work:
            with pytest.raises(KnowledgeObjectNotFound):
                unit_of_work.knowledge_objects.get(knowledge_object.header.id)

    def test_rollback_is_idempotent(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        with unit_of_work_factory() as unit_of_work:
            unit_of_work.rollback()
            unit_of_work.rollback()

    def test_both_repositories_participate_in_rollback(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        source = create_knowledge_object()
        target = create_knowledge_object(organization_id=source.header.organization_id)
        relation = create_relation(source=source, target=target)

        with pytest.raises(RuntimeError):
            with unit_of_work_factory() as unit_of_work:
                unit_of_work.knowledge_objects.add(source)
                unit_of_work.knowledge_objects.add(target)
                unit_of_work.relations.add(relation)
                raise RuntimeError("rollback")

        with unit_of_work_factory() as unit_of_work:
            with pytest.raises(KnowledgeObjectNotFound):
                unit_of_work.knowledge_objects.get(source.header.id)
            with pytest.raises(KnowledgeObjectRelationNotFound):
                unit_of_work.relations.get(relation.relation_id)

    def test_identity_and_audit_repositories_participate_in_rollback(
        self,
        unit_of_work_factory: Callable[[], UnitOfWorkContract],
    ) -> None:
        from datetime import UTC, datetime
        from uuid import uuid4

        from backend.core.domain.entities.audit_event import AuditEvent
        from backend.core.domain.entities.user import User, UserStatus
        from backend.core.domain.value_objects import OrganizationId, UserId
        from backend.core.domain.value_objects.audit_action import AuditAction
        from backend.core.domain.value_objects.audit_event_id import AuditEventId
        from backend.core.domain.value_objects.audit_outcome import AuditOutcome
        from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
        from backend.core.domain.exceptions import UserNotFound
        from backend.core.domain.exceptions.audit_event import AuditEventNotFound

        user = User(
            id=UserId(value=uuid4()),
            display_name="Operator",
            email="operator@example.com",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        event = AuditEvent(
            id=AuditEventId(value=uuid4()),
            actor_user_id=user.id,
            authorization_organization_id=OrganizationId(value=uuid4()),
            target_organization_id=None,
            action=AuditAction.USER_CREATE,
            resource_type=AuditResourceType.USER,
            resource_id=user.id.value,
            outcome=AuditOutcome.SUCCESS,
            failure_code=None,
            metadata={},
            occurred_at=datetime.now(UTC),
        )

        with pytest.raises(RuntimeError):
            with unit_of_work_factory() as unit_of_work:
                unit_of_work.users.add(user)
                unit_of_work.audit_events.add(event)
                raise RuntimeError("rollback")

        with unit_of_work_factory() as unit_of_work:
            with pytest.raises(UserNotFound):
                unit_of_work.users.get(user.id)
            with pytest.raises(AuditEventNotFound):
                unit_of_work.audit_events.get(event.id)

from __future__ import annotations

from uuid import uuid4

import pytest

from backend.core.application.audit.administrative_audit_recorder import (
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.failure_codes import DUPLICATE_USER_EMAIL
from backend.core.application.commands.create_user import CreateUserCommand
from backend.core.application.handlers.create_user import CreateUserHandler
from backend.core.domain.exceptions import DuplicateUserEmail
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_list_criteria import AuditEventListCriteria
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.value_objects.user_list_criteria import UserListCriteria
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork
from tests.core.audit_test_support import make_admin_audit_stack


def test_successful_user_creation_and_audit_event_commit_together() -> None:
    stack = make_admin_audit_stack()
    handler = CreateUserHandler(stack.uow, stack.audit)

    user = handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    events = stack.audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=stack.ctx.authorization_organization_id,
            offset=0,
            limit=10,
        )
    )

    assert stack.uow.committed is True
    assert events.total == 1
    assert events.items[0].action is AuditAction.USER_CREATE
    assert events.items[0].outcome is AuditOutcome.SUCCESS
    assert events.items[0].resource_id == user.id.value


def test_duplicate_user_failure_records_separate_failure_event() -> None:
    stack = make_admin_audit_stack()
    handler = CreateUserHandler(stack.uow, stack.audit)
    handler.handle(
        CreateUserCommand(
            email="operator@example.com",
            display_name="Safety Operator",
            audit_context=stack.ctx,
        )
    )

    with pytest.raises(DuplicateUserEmail):
        handler.handle(
            CreateUserCommand(
                email="operator@example.com",
                display_name="Another Operator",
                audit_context=stack.ctx,
            )
        )

    events = stack.audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=stack.ctx.authorization_organization_id,
            offset=0,
            limit=10,
            outcome=AuditOutcome.FAILURE,
        )
    )

    assert events.total == 1
    assert events.items[0].failure_code == DUPLICATE_USER_EMAIL


class FailingAuditUnitOfWork(InMemoryUnitOfWork):
    def commit(self) -> None:
        raise RuntimeError("audit persistence failed")


def test_audit_failure_during_successful_mutation_rolls_back_mutation() -> None:
    stack = make_admin_audit_stack()
    failing_uow = FailingAuditUnitOfWork(audit_events=stack.audit_events)
    handler = CreateUserHandler(failing_uow, stack.audit)

    with pytest.raises(RuntimeError, match="audit persistence failed"):
        handler.handle(
            CreateUserCommand(
                email="operator@example.com",
                display_name="Safety Operator",
                audit_context=stack.ctx,
            )
        )

    assert failing_uow.committed is False
    assert failing_uow.users.list_users(UserListCriteria(offset=0, limit=10)).total == 0

    success_events = stack.audit_events.list_events(
        AuditEventListCriteria(
            scope_organization_id=stack.ctx.authorization_organization_id,
            offset=0,
            limit=10,
            outcome=AuditOutcome.SUCCESS,
        )
    )
    assert success_events.total == 0


def test_record_failure_preserves_original_error_when_audit_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stack = make_admin_audit_stack()

    def failing_factory() -> InMemoryUnitOfWork:
        uow = InMemoryUnitOfWork(audit_events=stack.audit_events)

        class BrokenAuditRepo:
            def add(self, event: object) -> None:
                raise RuntimeError("failure audit persistence failed")

        uow._audit_events = BrokenAuditRepo()  # type: ignore[attr-defined]
        return uow

    audit = stack.audit
    audit._failure_uow_factory = failing_factory  # type: ignore[attr-defined]

    CreateUserHandler(stack.uow, audit).handle(
        CreateUserCommand(
            email="duplicate@example.com",
            display_name="First",
            audit_context=stack.ctx,
        )
    )

    with pytest.raises(DuplicateUserEmail):
        CreateUserHandler(stack.uow, audit).handle(
            CreateUserCommand(
                email="duplicate@example.com",
                display_name="Second",
                audit_context=stack.ctx,
            )
        )


def test_audit_record_spec_distinguishes_authorization_and_target_organization() -> None:
    actor = UserId(value=uuid4())
    auth_org = OrganizationId(value=uuid4())
    target_org = OrganizationId(value=uuid4())
    spec = AuditRecordSpec(
        action=AuditAction.MEMBERSHIP_CREATE,
        context=AuditContext(
            actor_user_id=actor,
            authorization_organization_id=auth_org,
        ),
        resource_type=AuditResourceType.MEMBERSHIP,
        target_organization_id=target_org,
    )

    assert spec.context.authorization_organization_id == auth_org
    assert spec.target_organization_id == target_org

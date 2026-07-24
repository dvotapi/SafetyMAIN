from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.handlers.list_audit_events import ListAuditEventsHandler
from backend.core.application.queries.audit_events import ListAuditEventsQuery
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.query_resolution import (
    UnknownSecurityEventNameError,
    audit_actions_for_category,
    audit_actions_for_significance,
    intersect_action_filters,
    resolve_security_event_name,
)
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryUnitOfWork,
)


def test_resolve_security_event_name_accepts_registered_names() -> None:
    assert (
        resolve_security_event_name("authentication.login.failed")
        is AuditAction.AUTHENTICATION_LOGIN_FAILED
    )


def test_resolve_security_event_name_rejects_unknown_and_empty() -> None:
    with pytest.raises(UnknownSecurityEventNameError):
        resolve_security_event_name("authentication.login.unknown")
    with pytest.raises(UnknownSecurityEventNameError):
        resolve_security_event_name("   ")


def test_category_and_severity_expand_to_registry_actions() -> None:
    auth_actions = audit_actions_for_category(SecurityEventCategory.AUTHENTICATION)
    assert AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED in auth_actions
    assert AuditAction.AUTHENTICATION_REFRESH_FAILED in auth_actions

    medium = audit_actions_for_significance(SecurityEventSignificance.MEDIUM)
    assert AuditAction.AUTHORIZATION_PERMISSION_DENIED in medium
    assert AuditAction.AUTHENTICATION_LOGIN_FAILED in medium
    assert AuditAction.USER_CREATE not in medium


def test_intersect_action_filters_uses_logical_and() -> None:
    left = frozenset(
        {
            AuditAction.AUTHENTICATION_LOGIN_FAILED,
            AuditAction.AUTHENTICATION_REFRESH_FAILED,
        }
    )
    right = frozenset(
        {
            AuditAction.AUTHENTICATION_LOGIN_FAILED,
            AuditAction.AUTHORIZATION_PERMISSION_DENIED,
        }
    )
    assert intersect_action_filters(left, right) == frozenset(
        {AuditAction.AUTHENTICATION_LOGIN_FAILED}
    )
    assert intersect_action_filters(None, left) == left
    assert intersect_action_filters(left, frozenset()) == frozenset()


def test_list_handler_maps_category_and_request_id_filters() -> None:
    scope = OrganizationId(value=uuid4())
    actor = UserId(value=uuid4())
    audit_events = InMemoryAuditEventRepository()
    matching = AuditEvent(
        id=AuditEventId(value=uuid4()),
        actor_user_id=actor,
        authorization_organization_id=scope,
        target_organization_id=None,
        action=AuditAction.AUTHENTICATION_LOGIN_FAILED,
        resource_type=AuditResourceType.SESSION,
        resource_id=actor.value,
        outcome=AuditOutcome.FAILURE,
        failure_code="invalid_credentials",
        metadata={"request_id": "req-handler-1"},
        occurred_at=datetime(2026, 7, 24, 10, 0, tzinfo=UTC),
    )
    audit_events.add(matching)
    audit_events.add(
        AuditEvent(
            id=AuditEventId(value=uuid4()),
            actor_user_id=actor,
            authorization_organization_id=scope,
            target_organization_id=None,
            action=AuditAction.USER_CREATE,
            resource_type=AuditResourceType.USER,
            resource_id=uuid4(),
            outcome=AuditOutcome.SUCCESS,
            failure_code=None,
            metadata={"request_id": "req-handler-1"},
            occurred_at=datetime(2026, 7, 24, 10, 1, tzinfo=UTC),
        )
    )
    handler = ListAuditEventsHandler(InMemoryUnitOfWork(audit_events=audit_events))

    result = handler.handle(
        ListAuditEventsQuery(
            scope_organization_id=scope,
            offset=0,
            limit=20,
            event_category=SecurityEventCategory.AUTHENTICATION,
            severity=SecurityEventSignificance.MEDIUM,
            request_id="req-handler-1",
            occurred_from=datetime(2026, 7, 24, 9, 0, tzinfo=UTC),
            occurred_to=datetime(2026, 7, 24, 11, 0, tzinfo=UTC),
        )
    )

    assert result.total == 1
    assert result.items[0].id == matching.id

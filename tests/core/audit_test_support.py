from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
)
from backend.core.contracts.clock import ClockContract
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryUnitOfWork,
)
from backend.core.infrastructure.time.utc_clock import UtcClock


@dataclass(frozen=True, slots=True)
class AdminAuditStack:
    uow: InMemoryUnitOfWork
    audit: AdministrativeAuditRecorder
    ctx: AuditContext
    audit_events: InMemoryAuditEventRepository


def make_admin_audit_stack(
    *,
    clock: ClockContract | None = None,
    actor_user_id: UserId | None = None,
    authorization_organization_id: OrganizationId | None = None,
    **uow_kwargs: object,
) -> AdminAuditStack:
    audit_events = InMemoryAuditEventRepository()
    uow = InMemoryUnitOfWork(audit_events=audit_events, **uow_kwargs)
    actor = actor_user_id or UserId(value=uuid4())
    auth_org = authorization_organization_id or OrganizationId(value=uuid4())
    ctx = AuditContext(
        actor_user_id=actor,
        authorization_organization_id=auth_org,
    )
    resolved_clock = clock or UtcClock()

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(audit_events=audit_events, **uow_kwargs)

    audit = AdministrativeAuditRecorder(resolved_clock, uow_factory)
    return AdminAuditStack(uow=uow, audit=audit, ctx=ctx, audit_events=audit_events)


def authenticated_audit_context(user_id: UserId) -> AuditContext:
    return AuditContext.for_authenticated_user(user_id)

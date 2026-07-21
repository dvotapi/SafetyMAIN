from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from backend.core.application.context.tenant_context import TenantContext
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

logger = logging.getLogger(__name__)

UowFactory = Callable[[], UnitOfWorkContract]


@dataclass(frozen=True, slots=True)
class AuditContext:
    actor_user_id: UserId | None
    authorization_organization_id: OrganizationId | None

    @classmethod
    def from_tenant(cls, tenant_context: TenantContext) -> AuditContext:
        return cls(
            actor_user_id=tenant_context.actor_user_id,
            authorization_organization_id=tenant_context.organization_id,
        )

    @classmethod
    def for_authenticated_user(cls, user_id: UserId) -> AuditContext:
        return cls(actor_user_id=user_id, authorization_organization_id=None)


@dataclass(frozen=True, slots=True)
class AuditRecordSpec:
    action: AuditAction
    context: AuditContext
    resource_type: AuditResourceType
    resource_id: UUID | None = None
    target_organization_id: OrganizationId | None = None
    metadata: dict[str, Any] | None = None
    failure_code: str | None = None


class AdministrativeAuditRecorder:
    def __init__(
        self,
        clock: ClockContract,
        failure_uow_factory: UowFactory,
    ) -> None:
        self._clock = clock
        self._failure_uow_factory = failure_uow_factory

    def record_success(
        self,
        unit_of_work: UnitOfWorkContract,
        spec: AuditRecordSpec,
    ) -> None:
        event = self._build_event(spec, outcome=AuditOutcome.SUCCESS)
        unit_of_work.audit_events.add(event)

    def record_known_failure(self, spec: AuditRecordSpec, error: Exception) -> None:
        from backend.core.application.audit.failure_codes import AUDITABLE_ADMIN_FAILURES

        failure_code = AUDITABLE_ADMIN_FAILURES.get(type(error))
        if failure_code is None:
            return
        self.record_failure(
            AuditRecordSpec(
                action=spec.action,
                context=spec.context,
                resource_type=spec.resource_type,
                resource_id=spec.resource_id,
                target_organization_id=spec.target_organization_id,
                metadata=spec.metadata,
                failure_code=failure_code,
            )
        )

    def record_failure(self, spec: AuditRecordSpec) -> None:
        if spec.failure_code is None:
            raise ValueError("Failure audit events require a failure code.")

        failure_spec = AuditRecordSpec(
            action=spec.action,
            context=spec.context,
            resource_type=spec.resource_type,
            resource_id=spec.resource_id,
            target_organization_id=spec.target_organization_id,
            metadata=spec.metadata,
            failure_code=spec.failure_code,
        )
        try:
            with self._failure_uow_factory() as unit_of_work:
                event = self._build_event(failure_spec, outcome=AuditOutcome.FAILURE)
                unit_of_work.audit_events.add(event)
                unit_of_work.commit()
        except Exception:
            logger.exception(
                "Failed to persist administrative audit failure event.",
                extra={
                    "audit_action": spec.action.value,
                    "audit_failure_code": spec.failure_code,
                    "actor_user_id": (
                        str(spec.context.actor_user_id.value)
                        if spec.context.actor_user_id
                        else None
                    ),
                    "authorization_organization_id": (
                        str(spec.context.authorization_organization_id.value)
                        if spec.context.authorization_organization_id
                        else None
                    ),
                },
            )

    def _build_event(self, spec: AuditRecordSpec, *, outcome: AuditOutcome) -> AuditEvent:
        return AuditEvent(
            id=AuditEventId(value=uuid4()),
            actor_user_id=spec.context.actor_user_id,
            authorization_organization_id=spec.context.authorization_organization_id,
            target_organization_id=spec.target_organization_id,
            action=spec.action,
            resource_type=spec.resource_type,
            resource_id=spec.resource_id,
            outcome=outcome,
            failure_code=spec.failure_code if outcome is AuditOutcome.FAILURE else None,
            metadata=spec.metadata or {},
            occurred_at=self._clock.now(),
        )


def audit_event_in_scope(event: AuditEvent, scope_organization_id: OrganizationId) -> bool:
    return (
        event.authorization_organization_id == scope_organization_id
        or event.target_organization_id == scope_organization_id
    )

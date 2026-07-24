from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.hazard_lifecycle import (
    ActivateHazardCommand,
    ArchiveHazardCommand,
    RestoreHazardCommand,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import HazardNotFound, HazardVersionConflict
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


def _load_hazard(
    unit_of_work: UnitOfWorkContract,
    command: ActivateHazardCommand | ArchiveHazardCommand | RestoreHazardCommand,
) -> Hazard:
    hazard = unit_of_work.hazards.get(command.organization_id, command.hazard_id)
    if hazard is None:
        raise HazardNotFound(command.hazard_id)
    if hazard.version != command.expected_version:
        raise HazardVersionConflict(
            hazard_id=hazard.id,
            expected_version=command.expected_version,
            actual_version=hazard.version,
        )
    return hazard


class ActivateHazardHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: ActivateHazardCommand) -> Hazard:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_HAZARD_ACTIVATED,
            context=audit_context,
            resource_type=AuditResourceType.HAZARD,
            resource_id=command.hazard_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> tuple[Hazard, str]:
            hazard = _load_hazard(self._unit_of_work, command)
            previous = hazard.status.value
            activated = hazard.activate(
                at=self._clock.now(),
                reviewed_by=command.actor_id,
            )
            return activated, previous

        def success_spec(result: tuple[Hazard, str]) -> AuditRecordSpec:
            hazard, previous = result
            self._unit_of_work.hazards.save(
                hazard,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_HAZARD_ACTIVATED,
                context=audit_context,
                resource_type=AuditResourceType.HAZARD,
                resource_id=hazard.id.value,
                target_organization_id=hazard.organization_id,
                metadata={
                    "hazard_id": str(hazard.id.value),
                    "hazard_code": hazard.code.value,
                    "previous_status": previous,
                    "new_status": hazard.status.value,
                    "category": hazard.category.value,
                    "safety_directions": [d.value for d in hazard.safety_directions],
                },
            )

        hazard, _previous = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return hazard


class ArchiveHazardHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: ArchiveHazardCommand) -> Hazard:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_HAZARD_ARCHIVED,
            context=audit_context,
            resource_type=AuditResourceType.HAZARD,
            resource_id=command.hazard_id.value,
            target_organization_id=command.organization_id,
            metadata={"reason": command.reason},
        )

        def operation() -> tuple[Hazard, str]:
            hazard = _load_hazard(self._unit_of_work, command)
            previous = hazard.status.value
            archived = hazard.archive(
                at=self._clock.now(),
                archived_by=command.actor_id,
                reason=command.reason,
            )
            return archived, previous

        def success_spec(result: tuple[Hazard, str]) -> AuditRecordSpec:
            hazard, previous = result
            self._unit_of_work.hazards.save(
                hazard,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_HAZARD_ARCHIVED,
                context=audit_context,
                resource_type=AuditResourceType.HAZARD,
                resource_id=hazard.id.value,
                target_organization_id=hazard.organization_id,
                metadata={
                    "hazard_id": str(hazard.id.value),
                    "hazard_code": hazard.code.value,
                    "previous_status": previous,
                    "new_status": hazard.status.value,
                    "reason": command.reason,
                },
            )

        hazard, _previous = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return hazard


class RestoreHazardHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: RestoreHazardCommand) -> Hazard:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_HAZARD_RESTORED,
            context=audit_context,
            resource_type=AuditResourceType.HAZARD,
            resource_id=command.hazard_id.value,
            target_organization_id=command.organization_id,
            metadata={"reason": command.reason},
        )

        def operation() -> tuple[Hazard, str]:
            hazard = _load_hazard(self._unit_of_work, command)
            previous = hazard.status.value
            restored = hazard.restore(
                at=self._clock.now(),
                restored_by=command.actor_id,
                reason=command.reason,
            )
            return restored, previous

        def success_spec(result: tuple[Hazard, str]) -> AuditRecordSpec:
            hazard, previous = result
            self._unit_of_work.hazards.save(
                hazard,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_HAZARD_RESTORED,
                context=audit_context,
                resource_type=AuditResourceType.HAZARD,
                resource_id=hazard.id.value,
                target_organization_id=hazard.organization_id,
                metadata={
                    "hazard_id": str(hazard.id.value),
                    "hazard_code": hazard.code.value,
                    "previous_status": previous,
                    "new_status": hazard.status.value,
                    "reason": command.reason,
                },
            )

        hazard, _previous = run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )
        return hazard

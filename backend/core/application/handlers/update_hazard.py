from __future__ import annotations

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.hazard_lifecycle import UpdateHazardCommand
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.exceptions.hazard import HazardNotFound
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class UpdateHazardHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        clock: ClockContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._audit = audit

    def handle(self, command: UpdateHazardCommand) -> Hazard:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.SAFETY_HAZARD_UPDATED,
            context=audit_context,
            resource_type=AuditResourceType.HAZARD,
            resource_id=command.hazard_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> Hazard:
            hazard = self._unit_of_work.hazards.get(
                command.organization_id,
                command.hazard_id,
            )
            if hazard is None:
                raise HazardNotFound(command.hazard_id)
            return hazard.update_details(
                at=self._clock.now(),
                expected_version=command.expected_version,
                title=command.title,
                description=command.description,
                category=command.category,
                safety_directions=command.safety_directions,
                source=command.source,
                affected_subjects=command.affected_subjects,
                location_reference=command.location_reference,
                process_reference=command.process_reference,
                equipment_reference=command.equipment_reference,
                extension_references=command.extension_references,
            )

        def success_spec(hazard: Hazard) -> AuditRecordSpec:
            self._unit_of_work.hazards.save(
                hazard,
                expected_version=command.expected_version,
            )
            return AuditRecordSpec(
                action=AuditAction.SAFETY_HAZARD_UPDATED,
                context=audit_context,
                resource_type=AuditResourceType.HAZARD,
                resource_id=hazard.id.value,
                target_organization_id=hazard.organization_id,
                metadata={
                    "hazard_id": str(hazard.id.value),
                    "hazard_code": hazard.code.value,
                    "category": hazard.category.value,
                    "safety_directions": [d.value for d in hazard.safety_directions],
                    "new_status": hazard.status.value,
                },
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )

from __future__ import annotations

from datetime import UTC, datetime

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.audit.metadata import changed_fields_metadata
from backend.core.application.commands.update_organization import UpdateOrganizationCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import Organization
from backend.core.domain.exceptions import DuplicateOrganizationName
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.domain.entities.organization import normalized_organization_name_key


class UpdateOrganizationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: UpdateOrganizationCommand) -> Organization:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.ORGANIZATION_UPDATE,
            context=audit_context,
            resource_type=AuditResourceType.ORGANIZATION,
            resource_id=command.organization_id.value,
            target_organization_id=command.organization_id,
        )

        def operation() -> Organization:
            organization = self._unit_of_work.organizations.get(command.organization_id)
            if organization.name == command.name:
                return organization
            normalized_name = normalized_organization_name_key(command.name)
            existing = self._unit_of_work.organizations.get_by_normalized_name(normalized_name)
            if existing is not None and existing.id != organization.id:
                raise DuplicateOrganizationName(command.name)
            return organization.model_copy(
                update={"name": command.name, "updated_at": datetime.now(UTC)}
            )

        def success_spec(organization: Organization) -> AuditRecordSpec:
            self._unit_of_work.organizations.save(organization)
            return AuditRecordSpec(
                action=AuditAction.ORGANIZATION_UPDATE,
                context=audit_context,
                resource_type=AuditResourceType.ORGANIZATION,
                resource_id=organization.id.value,
                target_organization_id=organization.id,
                metadata=changed_fields_metadata("name"),
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditRecordSpec,
)
from backend.core.application.audit.handler_support import (
    require_audit_context,
    run_audited_admin_operation,
)
from backend.core.application.commands.create_organization import CreateOrganizationCommand
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.organization import (
    Organization,
    OrganizationStatus,
    normalized_organization_name_key,
)
from backend.core.domain.exceptions import DuplicateOrganizationName
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


class CreateOrganizationHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWorkContract,
        audit: AdministrativeAuditRecorder,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._audit = audit

    def handle(self, command: CreateOrganizationCommand) -> Organization:
        audit_context = require_audit_context(command.audit_context)
        failure_spec = AuditRecordSpec(
            action=AuditAction.ORGANIZATION_CREATE,
            context=audit_context,
            resource_type=AuditResourceType.ORGANIZATION,
        )

        def operation() -> Organization:
            organization = Organization(
                id=OrganizationId(value=uuid4()),
                name=command.name,
                status=(
                    OrganizationStatus.ACTIVE
                    if command.is_active
                    else OrganizationStatus.DEACTIVATED
                ),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            normalized_name = normalized_organization_name_key(organization.name)
            if (
                self._unit_of_work.organizations.get_by_normalized_name(normalized_name)
                is not None
            ):
                raise DuplicateOrganizationName(organization.name)
            return organization

        def success_spec(organization: Organization) -> AuditRecordSpec:
            self._unit_of_work.organizations.add(organization)
            return AuditRecordSpec(
                action=AuditAction.ORGANIZATION_CREATE,
                context=audit_context,
                resource_type=AuditResourceType.ORGANIZATION,
                resource_id=organization.id.value,
                target_organization_id=organization.id,
            )

        return run_audited_admin_operation(
            self._audit,
            self._unit_of_work,
            failure_spec=failure_spec,
            operation=operation,
            success_spec=success_spec,
        )

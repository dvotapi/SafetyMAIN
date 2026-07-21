from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from backend.core.application.audit.administrative_audit_recorder import (
    AdministrativeAuditRecorder,
    AuditContext,
    AuditRecordSpec,
)
from backend.core.application.audit.failure_codes import AUDITABLE_ADMIN_FAILURES
from backend.core.contracts.unit_of_work import UnitOfWorkContract

T = TypeVar("T")


def require_audit_context(audit_context: AuditContext | None) -> AuditContext:
    if audit_context is None:
        raise ValueError("Audit context is required for administrative operations.")
    return audit_context


def _begin_transaction(unit_of_work: UnitOfWorkContract) -> None:
    begin = getattr(unit_of_work, "begin", None)
    if begin is not None:
        begin()


def run_audited_admin_operation(
    audit: AdministrativeAuditRecorder,
    unit_of_work: UnitOfWorkContract,
    *,
    failure_spec: AuditRecordSpec,
    operation: Callable[[], T],
    success_spec: Callable[[T], AuditRecordSpec],
) -> T:
    _begin_transaction(unit_of_work)
    try:
        result = operation()
        audit.record_success(unit_of_work, success_spec(result))
        unit_of_work.commit()
        return result
    except Exception as error:
        unit_of_work.rollback()
        if type(error) in AUDITABLE_ADMIN_FAILURES:
            audit.record_known_failure(failure_spec, error)
        raise

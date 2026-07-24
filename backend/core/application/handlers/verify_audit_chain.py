from __future__ import annotations

import logging

from backend.core.application.queries.verify_audit_chain import VerifyAuditChainQuery
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.services.audit_integrity_service import (
    AuditChainVerificationResult,
    AuditIntegrityService,
)

logger = logging.getLogger(__name__)


class VerifyAuditChainHandler:
    def __init__(self, unit_of_work: UnitOfWorkContract) -> None:
        self._unit_of_work = unit_of_work
        self._integrity = AuditIntegrityService()

    def handle(self, query: VerifyAuditChainQuery) -> AuditChainVerificationResult:
        events = self._unit_of_work.audit_events.list_chain_events(query.organization_id)
        chain_head = self._unit_of_work.audit_events.get_chain_head(query.organization_id)
        result = self._integrity.verify_chain(
            query.organization_id,
            events,
            chain_head=chain_head,
        )
        logger.info(
            "Audit integrity verification completed.",
            extra={
                "organization_id": str(query.organization_id.value),
                "valid": result.valid,
                "checked_event_count": result.checked_event_count,
                "first_invalid_event_id": (
                    str(result.first_invalid_event_id.value)
                    if result.first_invalid_event_id
                    else None
                ),
                "failure_reason": result.reason.value if result.reason else None,
            },
        )
        return result

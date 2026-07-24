"""Verify audit integrity chains for all organizations that have audit events.

Exit codes:
  0 — all chains valid
  1 — one or more chains invalid or verification failed
  2 — configuration / database error
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.services.audit_integrity_service import AuditIntegrityService
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_integrity import (
    PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID,
)
from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditChainHeadModel,
    AuditEventModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.audit_event_repository import (
    SQLAlchemyAuditEventRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.settings import get_database_url


def _organization_ids(session: Session) -> list[OrganizationId]:
    head_ids = {
        row[0]
        for row in session.execute(select(AuditChainHeadModel.organization_id)).all()
    }
    auth_ids = {
        row[0]
        for row in session.execute(
            select(distinct(AuditEventModel.authorization_organization_id)).where(
                AuditEventModel.authorization_organization_id.is_not(None)
            )
        ).all()
    }
    target_only = {
        row[0]
        for row in session.execute(
            select(distinct(AuditEventModel.target_organization_id)).where(
                AuditEventModel.authorization_organization_id.is_(None),
                AuditEventModel.target_organization_id.is_not(None),
            )
        ).all()
    }
    has_platform = session.scalar(
        select(AuditEventModel.id)
        .where(
            AuditEventModel.authorization_organization_id.is_(None),
            AuditEventModel.target_organization_id.is_(None),
        )
        .limit(1)
    )
    ids = set(head_ids) | set(auth_ids) | set(target_only)
    if has_platform is not None:
        ids.add(PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID)
    return [OrganizationId(value=value) for value in sorted(ids, key=str)]


def verify_all(session_factory: sessionmaker[Session]) -> int:
    integrity = AuditIntegrityService()
    failures = 0
    with session_factory() as session:
        repository = SQLAlchemyAuditEventRepository(session)
        organizations = _organization_ids(session)
        if not organizations:
            print("No audit integrity chains found.")
            return 0
        for organization_id in organizations:
            events = repository.list_chain_events(organization_id)
            result = integrity.verify_chain(
                organization_id,
                events,
                chain_head=repository.get_chain_head(organization_id),
            )
            if result.valid:
                print(
                    f"organization={organization_id.value} valid=true "
                    f"events={result.checked_event_count}"
                )
            else:
                failures += 1
                invalid_id = (
                    result.first_invalid_event_id.value
                    if result.first_invalid_event_id
                    else None
                )
                reason = result.reason.value if result.reason else "unknown"
                print(
                    f"organization={organization_id.value} valid=false "
                    f"events={result.checked_event_count} "
                    f"first_invalid_event={invalid_id} reason={reason}"
                )
    return 1 if failures else 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(list(argv) if argv is not None else None)
    try:
        engine = create_engine(get_database_url())
        session_factory = create_session_factory(engine)
        return verify_all(session_factory)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"verify_audit_integrity failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

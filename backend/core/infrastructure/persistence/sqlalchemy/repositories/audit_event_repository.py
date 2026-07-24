from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import asc, desc, func, or_, select, text
from sqlalchemy.orm import Session

from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.exceptions.audit_event import AuditEventNotFound
from backend.core.domain.repositories.audit_event_repository import (
    AuditEventRepositoryContract,
)
from backend.core.domain.services.audit_event_canonicalizer import (
    resolve_audit_chain_organization_id,
)
from backend.core.domain.services.audit_integrity_service import AuditIntegrityService
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.audit_chain_head import (
    AuditChainHead,
    organization_advisory_lock_key_text,
)
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_event_list_criteria import (
    AuditEventListCriteria,
    AuditEventListResult,
    effective_actions,
)
from backend.core.domain.value_objects.audit_integrity import (
    AuditIntegrityHash,
    AuditIntegrityVersion,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.audit_event_mapper import (
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.audit_event_model import (
    AuditChainHeadModel,
    AuditEventModel,
)


class SQLAlchemyAuditEventRepository(AuditEventRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._integrity = AuditIntegrityService()

    def add(self, event: AuditEvent) -> None:
        chain_org = resolve_audit_chain_organization_id(event)
        previous_hash = self._lock_chain_head(chain_org)
        draft = event.model_copy(
            update={
                "previous_integrity_hash": None,
                "integrity_hash": None,
                "integrity_version": None,
            }
        )
        finalized = self._integrity.finalize_event(draft, previous_hash)
        assert finalized.integrity_hash is not None
        self._session.add(to_model(finalized))
        self._upsert_chain_head(chain_org, finalized)

    def get(self, audit_event_id: AuditEventId) -> AuditEvent:
        model = self._session.get(AuditEventModel, audit_event_id.value)
        if model is None:
            raise AuditEventNotFound(audit_event_id)
        return to_domain(model)

    def list_events(self, criteria: AuditEventListCriteria) -> AuditEventListResult:
        filters = self._build_filters(criteria)
        actions = effective_actions(criteria)
        if actions is not None and not actions:
            return AuditEventListResult(
                items=(),
                total=0,
                offset=criteria.offset,
                limit=criteria.limit,
            )

        count_stmt = select(func.count()).select_from(AuditEventModel).where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)

        order_columns = (
            (asc(AuditEventModel.occurred_at), asc(AuditEventModel.id))
            if criteria.sort_ascending
            else (desc(AuditEventModel.occurred_at), desc(AuditEventModel.id))
        )
        stmt = (
            select(AuditEventModel)
            .where(*filters)
            .order_by(*order_columns)
            .offset(criteria.offset)
            .limit(criteria.limit)
        )
        models = self._session.scalars(stmt).all()
        page = tuple(to_domain(model) for model in models)

        return AuditEventListResult(
            items=page,
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def get_latest_integrity_hash(
        self,
        organization_id: OrganizationId,
    ) -> AuditIntegrityHash | None:
        head = self.get_chain_head(organization_id)
        return head.latest_integrity_hash if head is not None else None

    def get_chain_head(
        self,
        organization_id: OrganizationId,
    ) -> AuditChainHead | None:
        head = self._session.get(AuditChainHeadModel, organization_id.value)
        if head is None:
            return None
        return AuditChainHead(
            organization_id=OrganizationId(value=head.organization_id),
            latest_audit_event_id=AuditEventId(value=head.latest_audit_event_id),
            latest_integrity_hash=AuditIntegrityHash(value=head.latest_integrity_hash),
            integrity_version=AuditIntegrityVersion(value=head.integrity_version),
        )

    def list_chain_events(
        self,
        organization_id: OrganizationId,
    ) -> tuple[AuditEvent, ...]:
        from backend.core.domain.value_objects.audit_integrity import (
            PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID,
        )

        org_id = organization_id.value
        if org_id == PLATFORM_AUDIT_CHAIN_ORGANIZATION_ID:
            filters = [
                AuditEventModel.authorization_organization_id.is_(None),
                AuditEventModel.target_organization_id.is_(None),
            ]
        else:
            filters = [
                or_(
                    AuditEventModel.authorization_organization_id == org_id,
                    (
                        AuditEventModel.authorization_organization_id.is_(None)
                        & (AuditEventModel.target_organization_id == org_id)
                    ),
                )
            ]

        models = self._session.scalars(
            select(AuditEventModel)
            .where(*filters)
            .order_by(asc(AuditEventModel.occurred_at), asc(AuditEventModel.id))
        ).all()
        return tuple(to_domain(model) for model in models)

    def _lock_chain_head(
        self,
        organization_id: OrganizationId,
    ) -> AuditIntegrityHash | None:
        # Serialize appends per organization so concurrent genesis/appends cannot fork.
        # Transaction-scoped advisory lock + row lock; released on commit/rollback.
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:organization_id))"),
            {
                "organization_id": organization_advisory_lock_key_text(organization_id),
            },
        )
        head = self._session.execute(
            select(AuditChainHeadModel)
            .where(AuditChainHeadModel.organization_id == organization_id.value)
            .with_for_update()
        ).scalar_one_or_none()
        if head is None:
            return None
        return AuditIntegrityHash(value=head.latest_integrity_hash)

    def _upsert_chain_head(self, organization_id: OrganizationId, event: AuditEvent) -> None:
        assert event.integrity_hash is not None
        assert event.integrity_version is not None
        head = self._session.get(AuditChainHeadModel, organization_id.value)
        now = datetime.now(UTC)
        if head is None:
            self._session.add(
                AuditChainHeadModel(
                    organization_id=organization_id.value,
                    latest_audit_event_id=event.id.value,
                    latest_integrity_hash=event.integrity_hash.value,
                    integrity_version=event.integrity_version.value,
                    updated_at=now,
                )
            )
            return
        head.latest_audit_event_id = event.id.value
        head.latest_integrity_hash = event.integrity_hash.value
        head.integrity_version = event.integrity_version.value
        head.updated_at = now

    def _build_filters(self, criteria: AuditEventListCriteria) -> list[object]:
        scope_id = criteria.scope_organization_id.value
        filters: list[object] = [
            or_(
                AuditEventModel.authorization_organization_id == scope_id,
                AuditEventModel.target_organization_id == scope_id,
            )
        ]

        actions = effective_actions(criteria)
        if actions is not None:
            filters.append(AuditEventModel.action.in_([action.value for action in actions]))
        if criteria.resource_type is not None:
            filters.append(AuditEventModel.resource_type == criteria.resource_type.value)
        if criteria.resource_id is not None:
            filters.append(AuditEventModel.resource_id == criteria.resource_id)
        if criteria.actor_user_id is not None:
            filters.append(AuditEventModel.actor_user_id == criteria.actor_user_id.value)
        if criteria.outcome is not None:
            filters.append(AuditEventModel.outcome == criteria.outcome.value)
        if criteria.target_organization_id is not None:
            filters.append(
                AuditEventModel.target_organization_id
                == criteria.target_organization_id.value
            )
        if criteria.request_id is not None:
            filters.append(
                AuditEventModel.metadata_json["request_id"].as_string()
                == criteria.request_id
            )
        if criteria.occurred_from is not None:
            filters.append(AuditEventModel.occurred_at >= criteria.occurred_from)
        if criteria.occurred_to is not None:
            filters.append(AuditEventModel.occurred_at < criteria.occurred_to)

        return filters

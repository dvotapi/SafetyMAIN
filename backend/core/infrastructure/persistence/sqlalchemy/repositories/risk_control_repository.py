from __future__ import annotations

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.risk_control import RiskControl
from backend.core.domain.exceptions.risk_control import (
    DuplicateRiskControlCode,
    RiskControlNotFound,
    RiskControlVersionConflict,
)
from backend.core.domain.repositories.risk_control_repository import (
    RiskControlRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_control_code import RiskControlCode
from backend.core.domain.value_objects.risk_control_query import (
    RiskControlPage,
    RiskControlQuery,
)
from backend.core.domain.value_objects.safety_enums import RiskControlStatus
from backend.core.domain.value_objects.safety_ids import (
    RiskAssessmentId,
    RiskControlId,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.risk_control_mapper import (
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.risk_control_model import (
    RiskControlModel,
)

_TERMINAL = (
    RiskControlStatus.SUPERSEDED.value,
    RiskControlStatus.ARCHIVED.value,
    RiskControlStatus.CANCELLED.value,
)


class SQLAlchemyRiskControlRepository(RiskControlRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, control: RiskControl) -> None:
        existing = self.get_by_code(control.organization_id, control.code)
        if existing is not None:
            raise DuplicateRiskControlCode(
                organization_id=control.organization_id,
                code=control.code.value,
            )
        self._session.add(to_model(control))
        try:
            self._session.flush()
        except IntegrityError as error:
            message = str(error.orig)
            if "uq_risk_controls_organization_id_code" in message:
                raise DuplicateRiskControlCode(
                    organization_id=control.organization_id,
                    code=control.code.value,
                ) from error
            if "uq_risk_controls_org_assessment_source_ref" in message:
                raise DuplicateRiskControlCode(
                    organization_id=control.organization_id,
                    code=control.code.value,
                ) from error
            raise

    def get(
        self,
        organization_id: OrganizationId,
        control_id: RiskControlId,
    ) -> RiskControl | None:
        model = self._session.scalar(
            select(RiskControlModel).where(
                RiskControlModel.id == control_id.value,
                RiskControlModel.organization_id == organization_id.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskControlCode,
    ) -> RiskControl | None:
        model = self._session.scalar(
            select(RiskControlModel).where(
                RiskControlModel.organization_id == organization_id.value,
                RiskControlModel.code == code.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def exists_for_source(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
        source_control_reference: str,
    ) -> bool:
        model = self._session.scalar(
            select(RiskControlModel.id).where(
                RiskControlModel.organization_id == organization_id.value,
                RiskControlModel.risk_assessment_id == risk_assessment_id.value,
                RiskControlModel.source_control_reference == source_control_reference,
            )
        )
        return model is not None

    def list(self, query: RiskControlQuery) -> RiskControlPage:
        filters: list[object] = [
            RiskControlModel.organization_id == query.organization_id.value
        ]
        if not query.include_terminal:
            filters.append(RiskControlModel.lifecycle_status.notin_(_TERMINAL))
        if query.hazard_id is not None:
            filters.append(RiskControlModel.hazard_id == query.hazard_id.value)
        if query.risk_assessment_id is not None:
            filters.append(
                RiskControlModel.risk_assessment_id == query.risk_assessment_id.value
            )
        if query.status is not None:
            filters.append(RiskControlModel.lifecycle_status == query.status.value)
        if query.hierarchy_level is not None:
            filters.append(
                RiskControlModel.hierarchy_level == query.hierarchy_level.value
            )
        if query.control_nature is not None:
            filters.append(
                RiskControlModel.control_nature == query.control_nature.value
            )
        if query.owner_reference is not None:
            filters.append(RiskControlModel.owner_reference == query.owner_reference)
        if query.latest_effectiveness_result is not None:
            filters.append(
                RiskControlModel.latest_effectiveness_result
                == query.latest_effectiveness_result.value
            )
        if query.review_due_before is not None:
            filters.append(RiskControlModel.next_review_date <= query.review_due_before)
        if query.review_due_after is not None:
            filters.append(RiskControlModel.next_review_date >= query.review_due_after)
        if query.awaiting_verification:
            filters.append(
                RiskControlModel.lifecycle_status
                == RiskControlStatus.IMPLEMENTED.value
            )
        if query.created_from is not None:
            filters.append(RiskControlModel.created_at >= query.created_from)
        if query.created_to is not None:
            filters.append(RiskControlModel.created_at <= query.created_to)
        if query.updated_from is not None:
            filters.append(RiskControlModel.updated_at >= query.updated_from)
        if query.updated_to is not None:
            filters.append(RiskControlModel.updated_at <= query.updated_to)
        if query.search is not None and query.search.strip():
            pattern = f"%{query.search.strip()}%"
            filters.append(
                or_(
                    RiskControlModel.code.ilike(pattern),
                    RiskControlModel.title.ilike(pattern),
                    RiskControlModel.description.ilike(pattern),
                )
            )
        where_clause = and_(*filters)
        if query.overdue_only:
            as_of = query.as_of
            if as_of is None:
                raise ValueError("as_of is required when overdue_only is true.")
            all_models = self._session.scalars(
                select(RiskControlModel).where(where_clause)
            ).all()
            all_items = [
                item
                for item in (to_domain(model) for model in all_models)
                if item.is_overdue_for_review(as_of=as_of)
            ]
            total = len(all_items)
            page = all_items[query.offset : query.offset + query.limit]
            return RiskControlPage(
                items=tuple(page),
                total=total,
                offset=query.offset,
                limit=query.limit,
            )
        total = self._session.scalar(
            select(func.count()).select_from(RiskControlModel).where(where_clause)
        )
        assert total is not None
        models = self._session.scalars(
            select(RiskControlModel)
            .where(where_clause)
            .order_by(RiskControlModel.created_at.desc(), RiskControlModel.id.desc())
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        return RiskControlPage(
            items=tuple(to_domain(model) for model in models),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def save(self, control: RiskControl, *, expected_version: int) -> None:
        mapped = to_model(control)
        result = self._session.execute(
            update(RiskControlModel)
            .where(
                RiskControlModel.id == control.id.value,
                RiskControlModel.organization_id == control.organization_id.value,
                RiskControlModel.version == expected_version,
            )
            .values(
                code=mapped.code,
                title=mapped.title,
                description=mapped.description,
                hierarchy_level=mapped.hierarchy_level,
                control_nature=mapped.control_nature,
                source_type=mapped.source_type,
                source_reference=mapped.source_reference,
                hazard_id=mapped.hazard_id,
                risk_assessment_id=mapped.risk_assessment_id,
                source_control_reference=mapped.source_control_reference,
                source_payload=mapped.source_payload,
                scope=mapped.scope,
                owner=mapped.owner,
                owner_reference=mapped.owner_reference,
                owner_history=mapped.owner_history,
                implementation=mapped.implementation,
                evidence=mapped.evidence,
                verifications=mapped.verifications,
                review_schedule=mapped.review_schedule,
                competency_requirements=mapped.competency_requirements,
                related_entities=mapped.related_entities,
                extension_data=mapped.extension_data,
                lifecycle_status=mapped.lifecycle_status,
                latest_effectiveness_result=mapped.latest_effectiveness_result,
                next_review_date=mapped.next_review_date,
                verification_method_requirement=mapped.verification_method_requirement,
                suspension=mapped.suspension,
                status_before_suspension=mapped.status_before_suspension,
                superseded_by_id=mapped.superseded_by_id,
                cancel_reason=mapped.cancel_reason,
                archive_reason=mapped.archive_reason,
                updated_at=mapped.updated_at,
                updated_by=mapped.updated_by,
                version=mapped.version,
            )
        )
        if result.rowcount != 1:
            existing = self.get(control.organization_id, control.id)
            if existing is None:
                raise RiskControlNotFound(control.id)
            raise RiskControlVersionConflict(
                control_id=control.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )

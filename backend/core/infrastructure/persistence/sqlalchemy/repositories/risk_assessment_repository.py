from __future__ import annotations

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.domain.entities.risk_assessment import RiskAssessment
from backend.core.domain.exceptions.risk_assessment import (
    DuplicateRiskAssessmentCode,
    RiskAssessmentNotFound,
    RiskAssessmentVersionConflict,
)
from backend.core.domain.repositories.risk_assessment_repository import (
    RiskAssessmentRepositoryContract,
)
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.risk_assessment_code import RiskAssessmentCode
from backend.core.domain.value_objects.risk_assessment_components import (
    AssessedObjectRef,
)
from backend.core.domain.value_objects.risk_assessment_query import (
    RiskAssessmentPage,
    RiskAssessmentQuery,
)
from backend.core.domain.value_objects.safety_enums import (
    AssessmentProfileCode,
    RiskAssessmentStatus,
)
from backend.core.domain.value_objects.safety_ids import HazardId, RiskAssessmentId
from backend.core.infrastructure.persistence.sqlalchemy.mappers.risk_assessment_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.risk_assessment_model import (
    RiskAssessmentModel,
)


class SQLAlchemyRiskAssessmentRepository(RiskAssessmentRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, assessment: RiskAssessment) -> None:
        existing = self.get_by_code(assessment.organization_id, assessment.code)
        if existing is not None:
            raise DuplicateRiskAssessmentCode(
                organization_id=assessment.organization_id,
                code=assessment.code.value,
            )
        self._session.add(to_model(assessment))
        try:
            self._session.flush()
        except IntegrityError as error:
            if "uq_risk_assessments_organization_id_code" in str(error.orig):
                raise DuplicateRiskAssessmentCode(
                    organization_id=assessment.organization_id,
                    code=assessment.code.value,
                ) from error
            raise

    def get(
        self,
        organization_id: OrganizationId,
        risk_assessment_id: RiskAssessmentId,
    ) -> RiskAssessment | None:
        model = self._session.scalar(
            select(RiskAssessmentModel).where(
                RiskAssessmentModel.id == risk_assessment_id.value,
                RiskAssessmentModel.organization_id == organization_id.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: RiskAssessmentCode,
    ) -> RiskAssessment | None:
        model = self._session.scalar(
            select(RiskAssessmentModel).where(
                RiskAssessmentModel.organization_id == organization_id.value,
                RiskAssessmentModel.code == code.value,
            )
        )
        if model is None:
            return None
        return to_domain(model)

    def list(self, query: RiskAssessmentQuery) -> RiskAssessmentPage:
        filters: list[object] = [
            RiskAssessmentModel.organization_id == query.organization_id.value
        ]
        if not query.include_archived:
            filters.append(
                RiskAssessmentModel.status != RiskAssessmentStatus.ARCHIVED.value
            )
        if not query.include_superseded:
            filters.append(
                RiskAssessmentModel.status != RiskAssessmentStatus.SUPERSEDED.value
            )
        if query.hazard_id is not None:
            filters.append(RiskAssessmentModel.hazard_id == query.hazard_id.value)
        if query.status is not None:
            filters.append(RiskAssessmentModel.status == query.status.value)
        if query.assessment_profile is not None:
            filters.append(
                RiskAssessmentModel.assessment_profile
                == query.assessment_profile.value
            )
        if query.assessed_object_type is not None:
            filters.append(
                RiskAssessmentModel.assessed_object_type == query.assessed_object_type
            )
        if query.created_from is not None:
            filters.append(RiskAssessmentModel.created_at >= query.created_from)
        if query.created_to is not None:
            filters.append(RiskAssessmentModel.created_at <= query.created_to)
        if query.search is not None and query.search.strip():
            pattern = f"%{query.search.strip()}%"
            filters.append(
                or_(
                    RiskAssessmentModel.code.ilike(pattern),
                    RiskAssessmentModel.title.ilike(pattern),
                )
            )
        where_clause = and_(*filters)
        total = self._session.scalar(
            select(func.count()).select_from(RiskAssessmentModel).where(where_clause)
        )
        assert total is not None
        models = self._session.scalars(
            select(RiskAssessmentModel)
            .where(where_clause)
            .order_by(
                RiskAssessmentModel.created_at.desc(),
                RiskAssessmentModel.id.desc(),
            )
            .offset(query.offset)
            .limit(query.limit)
        ).all()
        return RiskAssessmentPage(
            items=tuple(to_domain(model) for model in models),
            total=total,
            offset=query.offset,
            limit=query.limit,
        )

    def list_approved_for_scope(
        self,
        *,
        organization_id: OrganizationId,
        hazard_id: HazardId,
        assessment_profile: AssessmentProfileCode,
        assessed_object: AssessedObjectRef,
    ) -> tuple[RiskAssessment, ...]:
        models = self._session.scalars(
            select(RiskAssessmentModel).where(
                RiskAssessmentModel.organization_id == organization_id.value,
                RiskAssessmentModel.hazard_id == hazard_id.value,
                RiskAssessmentModel.assessment_profile == assessment_profile.value,
                RiskAssessmentModel.assessed_object_type
                == assessed_object.object_type.value,
                RiskAssessmentModel.assessed_object_reference
                == assessed_object.reference,
                RiskAssessmentModel.status == RiskAssessmentStatus.APPROVED.value,
            )
        ).all()
        return tuple(to_domain(model) for model in models)

    def save(self, assessment: RiskAssessment, *, expected_version: int) -> None:
        result = self._session.execute(
            update(RiskAssessmentModel)
            .where(
                RiskAssessmentModel.id == assessment.id.value,
                RiskAssessmentModel.organization_id == assessment.organization_id.value,
                RiskAssessmentModel.version == expected_version,
            )
            .values(
                code=assessment.code.value,
                title=assessment.title,
                assessment_profile=assessment.assessment_profile.value,
                assessed_object_type=assessment.assessed_object.object_type.value,
                assessed_object_reference=assessment.assessed_object.reference,
                assessor_id=assessment.assessor_id.value,
                assessment_date=assessment.assessment_date,
                review_schedule=to_model(assessment).review_schedule,
                inherent_risk=to_model(assessment).inherent_risk,
                residual_risk=to_model(assessment).residual_risk,
                controls=to_model(assessment).controls,
                acceptance=to_model(assessment).acceptance,
                competency_requirements=to_model(assessment).competency_requirements,
                extension_references=dict(assessment.extension_references),
                status=assessment.status.value,
                superseded_by_id=(
                    None
                    if assessment.superseded_by_id is None
                    else assessment.superseded_by_id.value
                ),
                archived_at=assessment.archived_at,
                archived_by=(
                    None
                    if assessment.archived_by is None
                    else assessment.archived_by.value
                ),
                approved_at=assessment.approved_at,
                approved_by=(
                    None
                    if assessment.approved_by is None
                    else assessment.approved_by.value
                ),
                updated_at=assessment.updated_at,
                version=assessment.version,
            )
        )
        if result.rowcount == 0:
            existing = self.get(assessment.organization_id, assessment.id)
            if existing is None:
                raise RiskAssessmentNotFound(assessment.id)
            raise RiskAssessmentVersionConflict(
                risk_assessment_id=assessment.id,
                expected_version=expected_version,
                actual_version=existing.version,
            )
        model = self._session.get(RiskAssessmentModel, assessment.id.value)
        if model is not None:
            apply_to_model(model, assessment)

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.domain.entities.membership import Membership
from backend.core.domain.exceptions import MembershipByIdNotFound, MembershipNotFound
from backend.core.domain.repositories import MembershipRepositoryContract
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId
from backend.core.domain.value_objects.membership_list_criteria import (
    MembershipListCriteria,
    MembershipListResult,
)
from backend.core.infrastructure.persistence.sqlalchemy.mappers.membership_mapper import (
    apply_to_model,
    to_domain,
    to_model,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.membership_model import (
    MembershipModel,
)


class SQLAlchemyMembershipRepository(MembershipRepositoryContract):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, membership: Membership) -> None:
        self._session.add(to_model(membership))

    def get(self, membership_id: MembershipId) -> Membership:
        model = self._session.get(MembershipModel, membership_id.value)
        if model is None:
            raise MembershipByIdNotFound(membership_id)
        return to_domain(model)

    def get_by_user_and_organization(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        statement = select(MembershipModel).where(
            MembershipModel.user_id == user_id.value,
            MembershipModel.organization_id == organization_id.value,
        )
        model = self._session.scalar(statement)
        if model is None:
            return None
        return to_domain(model)

    def list_by_user(self, user_id: UserId) -> tuple[Membership, ...]:
        statement = select(MembershipModel).where(MembershipModel.user_id == user_id.value)
        models = self._session.scalars(statement).all()
        return tuple(to_domain(model) for model in models)

    def list_by_organization(self, organization_id: OrganizationId) -> tuple[Membership, ...]:
        statement = select(MembershipModel).where(
            MembershipModel.organization_id == organization_id.value
        )
        models = self._session.scalars(statement).all()
        return tuple(to_domain(model) for model in models)

    def list_active_by_user(self, user_id: UserId) -> tuple[Membership, ...]:
        statement = select(MembershipModel).where(
            MembershipModel.user_id == user_id.value,
            MembershipModel.is_active.is_(True),
        )
        models = self._session.scalars(statement).all()
        return tuple(to_domain(model) for model in models)

    def list_memberships(self, criteria: MembershipListCriteria) -> MembershipListResult:
        filters: list[object] = [
            MembershipModel.organization_id == criteria.organization_id.value
        ]
        if criteria.user_id is not None:
            filters.append(MembershipModel.user_id == criteria.user_id.value)
        if criteria.role is not None:
            filters.append(MembershipModel.role == criteria.role.value)
        if criteria.is_active is not None:
            filters.append(MembershipModel.is_active == criteria.is_active)

        count_statement = select(func.count()).select_from(MembershipModel).where(*filters)
        total = int(self._session.scalar(count_statement) or 0)

        statement = select(MembershipModel).where(*filters)
        if criteria.sort_ascending:
            order_clause = (
                MembershipModel.created_at.asc(),
                MembershipModel.id.asc(),
            )
        else:
            order_clause = (
                MembershipModel.created_at.desc(),
                MembershipModel.id.asc(),
            )
        models = self._session.scalars(
            statement.order_by(*order_clause)
            .offset(criteria.offset)
            .limit(criteria.limit)
        ).all()

        return MembershipListResult(
            items=tuple(to_domain(model) for model in models),
            total=total,
            offset=criteria.offset,
            limit=criteria.limit,
        )

    def save(self, membership: Membership) -> None:
        model = self._session.get(MembershipModel, membership.id.value)
        if model is None:
            raise MembershipNotFound(
                user_id=membership.user_id,
                organization_id=membership.organization_id,
            )
        apply_to_model(model, membership)

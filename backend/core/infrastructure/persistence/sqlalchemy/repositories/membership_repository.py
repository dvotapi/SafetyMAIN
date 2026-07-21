from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.domain.entities.membership import Membership
from backend.core.domain.exceptions import MembershipNotFound
from backend.core.domain.repositories import MembershipRepositoryContract
from backend.core.domain.value_objects import MembershipId, OrganizationId, UserId
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
            raise MembershipNotFound(
                user_id=UserId(value=membership_id.value),
                organization_id=OrganizationId(value=membership_id.value),
            )
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

    def save(self, membership: Membership) -> None:
        model = self._session.get(MembershipModel, membership.id.value)
        if model is None:
            raise MembershipNotFound(
                user_id=membership.user_id,
                organization_id=membership.organization_id,
            )
        apply_to_model(model, membership)

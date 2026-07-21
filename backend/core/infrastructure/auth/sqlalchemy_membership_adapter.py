from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.domain.entities.membership import Membership
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.infrastructure.persistence.sqlalchemy.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.session_scope import read_in_session


class SQLAlchemyMembershipAdapter(MembershipLookupPort, MembershipVerificationPort):
    """SQLAlchemy-backed membership lookup for authorization."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def register_membership(self, membership: Membership) -> None:
        def _register(session: Session) -> None:
            SQLAlchemyMembershipRepository(session).add(membership)

        from backend.core.infrastructure.persistence.sqlalchemy.session_scope import (
            run_in_session,
        )

        run_in_session(self._session_factory, _register)

    def get_membership(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> Membership | None:
        def _get_membership(session: Session) -> Membership | None:
            return SQLAlchemyMembershipRepository(session).get_by_user_and_organization(
                user_id,
                organization_id,
            )

        return read_in_session(self._session_factory, _get_membership)

    def list_memberships_for_user(self, user_id: UserId) -> tuple[Membership, ...]:
        def _list_memberships(session: Session) -> tuple[Membership, ...]:
            return SQLAlchemyMembershipRepository(session).list_by_user(user_id)

        return read_in_session(self._session_factory, _list_memberships)

    def is_active_member(
        self,
        user_id: UserId,
        organization_id: OrganizationId,
    ) -> bool:
        membership = self.get_membership(user_id, organization_id)
        if membership is None:
            return False
        return membership.grants_organization_access()

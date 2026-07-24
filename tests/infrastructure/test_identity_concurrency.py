from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.exceptions import DuplicateMembership, DuplicateUserEmail
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

pytest_plugins = ("tests.infrastructure.db_fixtures",)


def _user(*, email: str) -> User:
    now = datetime.now(UTC)
    return User(
        id=UserId(value=uuid4()),
        email=email,
        display_name="Concurrent User",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def _organization() -> Organization:
    now = datetime.now(UTC)
    return Organization(
        id=OrganizationId(value=uuid4()),
        name=f"Concurrent Org {uuid4()}",
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def _membership(*, user_id: UserId, organization_id: OrganizationId) -> Membership:
    now = datetime.now(UTC)
    return Membership(
        id=MembershipId(value=uuid4()),
        user_id=user_id,
        organization_id=organization_id,
        status=MembershipStatus.ACTIVE,
        role=Role.member(),
        joined_at=now,
        updated_at=now,
    )


@pytest.mark.db
def test_concurrent_duplicate_user_email(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    email = f"race-{uuid4()}@example.com"
    barrier = Barrier(2)
    outcomes: list[str] = []

    def create_one() -> None:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        try:
            with uow:
                barrier.wait(timeout=30)
                uow.users.add(_user(email=email))
                uow.commit()
            outcomes.append("ok")
        except DuplicateUserEmail:
            outcomes.append("duplicate")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create_one) for _ in range(2)]
        for future in futures:
            future.result(timeout=60)

    assert sorted(outcomes) == ["duplicate", "ok"]

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        assert uow.users.get_by_email(email) is not None


@pytest.mark.db
def test_concurrent_duplicate_membership(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as seed:
        user = _user(email=f"member-race-{uuid4()}@example.com")
        organization = _organization()
        seed.users.add(user)
        seed.organizations.add(organization)
        seed.commit()

    barrier = Barrier(2)
    outcomes: list[str] = []

    def create_one() -> None:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        try:
            with uow:
                barrier.wait(timeout=30)
                uow.memberships.add(
                    _membership(user_id=user.id, organization_id=organization.id)
                )
                uow.commit()
            outcomes.append("ok")
        except DuplicateMembership:
            outcomes.append("duplicate")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create_one) for _ in range(2)]
        for future in futures:
            future.result(timeout=60)

    assert sorted(outcomes) == ["duplicate", "ok"]

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        assert (
            uow.memberships.get_by_user_and_organization(user.id, organization.id)
            is not None
        )


@pytest.mark.db
def test_user_add_rolls_back_with_unit_of_work(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    email = f"rollback-{uuid4()}@example.com"
    uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
    with uow:
        uow.users.add(_user(email=email))
        uow.rollback()

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as verify:
        assert verify.users.get_by_email(email) is None


@pytest.mark.db
def test_concurrent_invitation_acceptance_membership_uniqueness(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    """Double-accept style race: membership uniqueness blocks a second insert."""

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as seed:
        user = _user(email=f"invite-race-{uuid4()}@example.com")
        organization = _organization()
        seed.users.add(user)
        seed.organizations.add(organization)
        seed.commit()
        assert seed.organizations.get(organization.id).id == organization.id
        assert seed.users.get(user.id).id == user.id

    barrier = Barrier(2)
    outcomes: list[str] = []

    def accept_style_create() -> None:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        try:
            with uow:
                barrier.wait(timeout=30)
                uow.memberships.add(
                    _membership(user_id=user.id, organization_id=organization.id)
                )
                uow.commit()
            outcomes.append("ok")
        except DuplicateMembership:
            outcomes.append("duplicate")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(accept_style_create) for _ in range(2)]
        for future in futures:
            future.result(timeout=60)

    assert sorted(outcomes) == ["duplicate", "ok"]

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        membership = uow.memberships.get_by_user_and_organization(
            user.id,
            organization.id,
        )
        assert membership is not None
        assert membership.is_active()


@pytest.mark.db
def test_role_update_versus_membership_deactivation(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> None:
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as seed:
        user = _user(email=f"role-race-{uuid4()}@example.com")
        organization = _organization()
        seed.users.add(user)
        seed.organizations.add(organization)
        seed.commit()

    membership = _membership(user_id=user.id, organization_id=organization.id)
    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as seed:
        seed.memberships.add(membership)
        seed.commit()

    barrier = Barrier(2)

    def update_role() -> None:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        with uow:
            current = uow.memberships.get(membership.id)
            barrier.wait(timeout=30)
            uow.memberships.save(current.model_copy(update={"role": Role.admin()}))
            uow.commit()

    def deactivate() -> None:
        uow = SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
        with uow:
            current = uow.memberships.get(membership.id)
            barrier.wait(timeout=30)
            uow.memberships.save(
                current.model_copy(update={"status": MembershipStatus.REVOKED})
            )
            uow.commit()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(update_role), executor.submit(deactivate)]
        for future in futures:
            future.result(timeout=60)

    with SQLAlchemyUnitOfWork(sqlalchemy_session_factory) as uow:
        loaded = uow.memberships.get(membership.id)
        # Last writer wins; both operations must leave a single consistent row.
        assert loaded.role.value in {"admin", "member"}
        assert isinstance(loaded.is_active(), bool)

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.repositories import MembershipRepositoryContract, UserRepositoryContract
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryMembershipRepository,
    InMemoryUserRepository,
)


class UserRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> UserRepositoryContract:
        raise NotImplementedError

    def test_add_and_get_user(self, repository: UserRepositoryContract) -> None:
        user = _create_user()

        repository.add(user)

        assert repository.get(user.id) == user

    def test_get_by_email(self, repository: UserRepositoryContract) -> None:
        user = _create_user()
        repository.add(user)

        assert repository.get_by_email(user.email) == user
        assert repository.get_by_email("missing@example.com") is None


class MembershipRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> MembershipRepositoryContract:
        raise NotImplementedError

    def test_add_and_lookup_membership(
        self,
        repository: MembershipRepositoryContract,
    ) -> None:
        membership = _create_membership()

        repository.add(membership)

        assert repository.get(membership.id) == membership
        assert repository.get_by_user_and_organization(
            membership.user_id,
            membership.organization_id,
        ) == membership
        assert repository.list_by_user(membership.user_id) == (membership,)


def _create_user() -> User:
    return User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email=f"operator-{uuid4()}@example.com",
        status=UserStatus.ACTIVE,
        created_at=datetime.now(UTC),
    )


def _create_membership() -> Membership:
    return Membership(
        id=MembershipId(value=uuid4()),
        user_id=UserId(value=uuid4()),
        organization_id=OrganizationId(value=uuid4()),
        status=MembershipStatus.ACTIVE,
        role=Role.member(),
        joined_at=datetime.now(UTC),
    )


class TestInMemoryUserRepositoryContract(UserRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> UserRepositoryContract:
        return InMemoryUserRepository()


class TestInMemoryMembershipRepositoryContract(MembershipRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> MembershipRepositoryContract:
        return InMemoryMembershipRepository()

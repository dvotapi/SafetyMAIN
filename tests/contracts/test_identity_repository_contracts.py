from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.entities.organization import Organization, OrganizationStatus
from backend.core.domain.repositories import (
    MembershipRepositoryContract,
    OrganizationRepositoryContract,
    UserRepositoryContract,
)
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
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

    def test_list_users_supports_filtering(self, repository: UserRepositoryContract) -> None:
        from backend.core.domain.value_objects.user_list_criteria import UserListCriteria

        active_user = _create_user()
        inactive_user = _create_user()
        inactive_user = inactive_user.model_copy(
            update={"email": f"inactive-{uuid4()}@example.com", "status": UserStatus.DEACTIVATED}
        )
        repository.add(active_user)
        repository.add(inactive_user)

        result = repository.list_users(
            UserListCriteria(offset=0, limit=10, is_active=True)
        )

        assert result.total == 1
        assert result.items[0].id == active_user.id


class OrganizationRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> OrganizationRepositoryContract:
        raise NotImplementedError

    def test_add_and_get_organization(
        self,
        repository: OrganizationRepositoryContract,
    ) -> None:
        organization = _create_organization()
        repository.add(organization)
        assert repository.get(organization.id) == organization

    def test_get_by_normalized_name(
        self,
        repository: OrganizationRepositoryContract,
    ) -> None:
        organization = _create_organization(name="Acme Safety")
        repository.add(organization)

        assert repository.get_by_normalized_name("acme safety") == organization
        assert repository.get_by_normalized_name("missing") is None

    def test_list_organizations_supports_filtering(
        self,
        repository: OrganizationRepositoryContract,
    ) -> None:
        from backend.core.domain.value_objects.organization_list_criteria import (
            OrganizationListCriteria,
        )

        active_org = _create_organization(name="Alpha Org")
        inactive_org = _create_organization(name="Beta Org").model_copy(
            update={"status": OrganizationStatus.DEACTIVATED}
        )
        repository.add(active_org)
        repository.add(inactive_org)

        result = repository.list_organizations(
            OrganizationListCriteria(offset=0, limit=10, is_active=True)
        )

        assert result.total == 1
        assert result.items[0].id == active_org.id


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
    now = datetime.now(UTC)
    return User(
        id=UserId(value=uuid4()),
        display_name="Safety Operator",
        email=f"operator-{uuid4()}@example.com",
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def _create_organization(*, name: str = "SafetyMAIN Development Organization") -> Organization:
    now = datetime.now(UTC)
    return Organization(
        id=OrganizationId(value=uuid4()),
        name=name,
        status=OrganizationStatus.ACTIVE,
        created_at=now,
        updated_at=now,
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


class TestInMemoryOrganizationRepositoryContract(OrganizationRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> OrganizationRepositoryContract:
        return InMemoryOrganizationRepository()


class TestInMemoryMembershipRepositoryContract(MembershipRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> MembershipRepositoryContract:
        return InMemoryMembershipRepository()

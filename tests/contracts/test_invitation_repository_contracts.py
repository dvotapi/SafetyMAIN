from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.domain.entities.invitation import Invitation, InvitationStatus
from backend.core.domain.repositories.invitation_repository import InvitationRepositoryContract
from backend.core.domain.value_objects import InvitationId, OrganizationId, Role, UserId
from backend.core.domain.value_objects.invitation_list_criteria import InvitationListCriteria
from backend.core.infrastructure.persistence.in_memory.invitation_repository import (
    InMemoryInvitationRepository,
)


class InvitationRepositoryContractSuite:
    @pytest.fixture()
    def repository(self) -> InvitationRepositoryContract:
        raise NotImplementedError

    def test_add_get_and_token_lookup(self, repository: InvitationRepositoryContract) -> None:
        invitation = _create_invitation()

        repository.add(invitation)

        assert repository.get(invitation.id) == invitation
        assert repository.get_by_token_hash(invitation.token_hash) == invitation

    def test_list_invitations_supports_filters(
        self,
        repository: InvitationRepositoryContract,
    ) -> None:
        organization_id = OrganizationId(value=uuid4())
        now = datetime.now(UTC)
        pending = _create_invitation(
            organization_id=organization_id,
            email="pending@example.com",
            now=now,
        )
        expired = _create_invitation(
            organization_id=organization_id,
            email="expired@example.com",
            now=now - timedelta(days=10),
            expires_at=now - timedelta(days=3),
        )
        repository.add(pending)
        repository.add(expired)

        result = repository.list_invitations(
            InvitationListCriteria(
                organization_id=organization_id,
                offset=0,
                limit=10,
                as_of=now,
                status=InvitationStatus.EXPIRED,
            )
        )

        assert result.total == 1
        assert result.items[0].id == expired.id

    def test_duplicate_detection_returns_pending_invitation(
        self,
        repository: InvitationRepositoryContract,
    ) -> None:
        organization_id = OrganizationId(value=uuid4())
        invitation = _create_invitation(
            organization_id=organization_id,
            email="invitee@example.com",
        )
        repository.add(invitation)

        assert (
            repository.get_active_pending_by_organization_and_email(
                organization_id,
                "invitee@example.com",
            )
            == invitation
        )


def _create_invitation(
    *,
    organization_id: OrganizationId | None = None,
    email: str | None = None,
    now: datetime | None = None,
    expires_at: datetime | None = None,
) -> Invitation:
    timestamp = now or datetime.now(UTC)
    return Invitation(
        id=InvitationId(value=uuid4()),
        organization_id=organization_id or OrganizationId(value=uuid4()),
        email=email or f"invitee-{uuid4()}@example.com",
        role=Role.member(),
        status=InvitationStatus.PENDING,
        token_hash=f"hash-{uuid4().hex}",
        expires_at=expires_at or timestamp + timedelta(days=7),
        created_by=UserId(value=uuid4()),
        created_at=timestamp,
        updated_at=timestamp,
    )


class TestInMemoryInvitationRepositoryContract(InvitationRepositoryContractSuite):
    @pytest.fixture()
    def repository(self) -> InvitationRepositoryContract:
        return InMemoryInvitationRepository()

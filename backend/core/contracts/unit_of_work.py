from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from backend.core.domain.repositories import (
    AuditEventRepositoryContract,
    InvitationRepositoryContract,
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
    MembershipRepositoryContract,
    OrganizationRepositoryContract,
    UserRepositoryContract,
)


class UnitOfWorkContract(Protocol):
    """Coordinates repository operations for an application use case."""

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        ...

    @property
    def relations(self) -> KnowledgeObjectRelationRepositoryContract:
        ...

    @property
    def users(self) -> UserRepositoryContract:
        ...

    @property
    def organizations(self) -> OrganizationRepositoryContract:
        ...

    @property
    def memberships(self) -> MembershipRepositoryContract:
        ...

    @property
    def invitations(self) -> InvitationRepositoryContract:
        ...

    @property
    def audit_events(self) -> AuditEventRepositoryContract:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

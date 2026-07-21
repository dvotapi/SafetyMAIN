from __future__ import annotations

from types import TracebackType

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.repositories import (
    AuditEventRepositoryContract,
    InvitationRepositoryContract,
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
    MembershipRepositoryContract,
    OrganizationRepositoryContract,
    UserRepositoryContract,
)
from backend.core.infrastructure.persistence.in_memory.audit_event_repository import (
    InMemoryAuditEventRepository,
)
from backend.core.infrastructure.persistence.in_memory.invitation_repository import (
    InMemoryInvitationRepository,
)
from backend.core.infrastructure.persistence.in_memory.knowledge_object_repository import (
    InMemoryKnowledgeObjectRepository,
)
from backend.core.infrastructure.persistence.in_memory.knowledge_object_relation_repository import (
    InMemoryKnowledgeObjectRelationRepository,
)
from backend.core.infrastructure.persistence.in_memory.membership_repository import (
    InMemoryMembershipRepository,
)
from backend.core.infrastructure.persistence.in_memory.organization_repository import (
    InMemoryOrganizationRepository,
)
from backend.core.infrastructure.persistence.in_memory.user_repository import (
    InMemoryUserRepository,
)


class InMemoryUnitOfWork(UnitOfWorkContract):
    def __init__(
        self,
        knowledge_objects: KnowledgeObjectRepositoryContract | None = None,
        relations: KnowledgeObjectRelationRepositoryContract | None = None,
        users: UserRepositoryContract | None = None,
        organizations: OrganizationRepositoryContract | None = None,
        memberships: MembershipRepositoryContract | None = None,
        invitations: InvitationRepositoryContract | None = None,
        audit_events: AuditEventRepositoryContract | None = None,
    ) -> None:
        self._knowledge_objects = knowledge_objects or InMemoryKnowledgeObjectRepository()
        self._relations = relations or InMemoryKnowledgeObjectRelationRepository()
        self._users = users or InMemoryUserRepository()
        self._organizations = organizations or InMemoryOrganizationRepository()
        self._memberships = memberships or InMemoryMembershipRepository()
        self._invitations = invitations or InMemoryInvitationRepository()
        self._audit_events = audit_events or InMemoryAuditEventRepository()
        self._knowledge_objects_snapshot: object | None = None
        self._relations_snapshot: object | None = None
        self._users_snapshot: object | None = None
        self._organizations_snapshot: object | None = None
        self._memberships_snapshot: object | None = None
        self._invitations_snapshot: object | None = None
        self._audit_events_snapshot: object | None = None
        self._snapshots_taken = False
        self._context_depth = 0
        self.committed = False
        self.rolled_back = False

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        return self._knowledge_objects

    @property
    def relations(self) -> KnowledgeObjectRelationRepositoryContract:
        return self._relations

    @property
    def users(self) -> UserRepositoryContract:
        return self._users

    @property
    def organizations(self) -> OrganizationRepositoryContract:
        return self._organizations

    @property
    def memberships(self) -> MembershipRepositoryContract:
        return self._memberships

    @property
    def invitations(self) -> InvitationRepositoryContract:
        return self._invitations

    @property
    def audit_events(self) -> AuditEventRepositoryContract:
        return self._audit_events

    def begin(self) -> None:
        if self._context_depth == 0:
            self._create_snapshots()

    def commit(self) -> None:
        self.committed = True
        if self._context_depth == 0:
            self._release_snapshots()

    def rollback(self) -> None:
        if self._snapshots_taken:
            self._restore_snapshots()
        self.committed = False
        self.rolled_back = True
        self._release_snapshots()

    def __enter__(self) -> InMemoryUnitOfWork:
        self._context_depth += 1
        if self._context_depth == 1:
            self.committed = False
            self.rolled_back = False
            self._create_snapshots()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None or not self.committed:
                self.rollback()
            elif self._snapshots_taken:
                self._release_snapshots()
        finally:
            self._context_depth = max(self._context_depth - 1, 0)

    def _create_snapshots(self) -> None:
        if self._snapshots_taken:
            return

        if hasattr(self._knowledge_objects, "snapshot"):
            self._knowledge_objects_snapshot = self._knowledge_objects.snapshot()
        if hasattr(self._relations, "snapshot"):
            self._relations_snapshot = self._relations.snapshot()
        if hasattr(self._users, "snapshot"):
            self._users_snapshot = self._users.snapshot()
        if hasattr(self._organizations, "snapshot"):
            self._organizations_snapshot = self._organizations.snapshot()
        if hasattr(self._memberships, "snapshot"):
            self._memberships_snapshot = self._memberships.snapshot()
        if hasattr(self._invitations, "snapshot"):
            self._invitations_snapshot = self._invitations.snapshot()
        if hasattr(self._audit_events, "snapshot"):
            self._audit_events_snapshot = self._audit_events.snapshot()
        self._snapshots_taken = True

    def _restore_snapshots(self) -> None:
        if (
            self._knowledge_objects_snapshot is not None
            and hasattr(self._knowledge_objects, "restore")
        ):
            self._knowledge_objects.restore(self._knowledge_objects_snapshot)
        if self._relations_snapshot is not None and hasattr(self._relations, "restore"):
            self._relations.restore(self._relations_snapshot)
        if self._users_snapshot is not None and hasattr(self._users, "restore"):
            self._users.restore(self._users_snapshot)
        if (
            self._organizations_snapshot is not None
            and hasattr(self._organizations, "restore")
        ):
            self._organizations.restore(self._organizations_snapshot)
        if self._memberships_snapshot is not None and hasattr(self._memberships, "restore"):
            self._memberships.restore(self._memberships_snapshot)
        if self._invitations_snapshot is not None and hasattr(self._invitations, "restore"):
            self._invitations.restore(self._invitations_snapshot)
        if self._audit_events_snapshot is not None and hasattr(self._audit_events, "restore"):
            self._audit_events.restore(self._audit_events_snapshot)

    def _release_snapshots(self) -> None:
        self._snapshots_taken = False
        self._knowledge_objects_snapshot = None
        self._relations_snapshot = None
        self._users_snapshot = None
        self._organizations_snapshot = None
        self._memberships_snapshot = None
        self._invitations_snapshot = None
        self._audit_events_snapshot = None

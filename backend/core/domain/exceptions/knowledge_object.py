from __future__ import annotations

from backend.core.domain.entities.knowledge_object import KnowledgeObjectStatus
from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectVersion,
)


class KnowledgeObjectError(SafetyMainDomainError):
    """Base class for Knowledge Object domain errors."""


class KnowledgeObjectNotFound(KnowledgeObjectError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            f"Knowledge Object was not found: {knowledge_object_id.value}"
        )


class KnowledgeObjectAlreadyArchived(KnowledgeObjectError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            f"Knowledge Object is already archived: {knowledge_object_id.value}"
        )


class KnowledgeObjectAlreadyActive(KnowledgeObjectError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            f"Knowledge Object is already active: {knowledge_object_id.value}"
        )


class KnowledgeObjectAlreadyDeleted(KnowledgeObjectError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            f"Knowledge Object is already deleted: {knowledge_object_id.value}"
        )


class InvalidKnowledgeObjectStateTransition(KnowledgeObjectError):
    def __init__(
        self,
        knowledge_object_id: KnowledgeObjectId,
        current_status: KnowledgeObjectStatus,
        requested_status: KnowledgeObjectStatus,
    ) -> None:
        self.knowledge_object_id = knowledge_object_id
        self.current_status = current_status
        self.requested_status = requested_status
        super().__init__(
            "Invalid Knowledge Object state transition: "
            f"{knowledge_object_id.value} from {current_status.value} "
            f"to {requested_status.value}"
        )


class KnowledgeObjectVersionConflict(KnowledgeObjectError):
    def __init__(
        self,
        knowledge_object_id: KnowledgeObjectId,
        expected_version: KnowledgeObjectVersion,
        actual_version: KnowledgeObjectVersion,
    ) -> None:
        self.knowledge_object_id = knowledge_object_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            "Knowledge Object version conflict: "
            f"{knowledge_object_id.value} expected version "
            f"{expected_version.value}, actual version {actual_version.value}"
        )


class DuplicateKnowledgeObject(KnowledgeObjectError):
    def __init__(self, knowledge_object_id: KnowledgeObjectId) -> None:
        self.knowledge_object_id = knowledge_object_id
        super().__init__(
            f"Knowledge Object already exists: {knowledge_object_id.value}"
        )

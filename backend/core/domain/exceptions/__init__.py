from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.exceptions.knowledge_object import (
    DuplicateKnowledgeObject,
    InvalidKnowledgeObjectStateTransition,
    KnowledgeObjectAlreadyActive,
    KnowledgeObjectAlreadyArchived,
    KnowledgeObjectAlreadyDeleted,
    KnowledgeObjectError,
    KnowledgeObjectNotFound,
    KnowledgeObjectVersionConflict,
)
from backend.core.domain.exceptions.knowledge_object_relation import (
    CrossOrganizationKnowledgeObjectRelation,
    DuplicateKnowledgeObjectRelation,
    KnowledgeObjectRelationError,
    KnowledgeObjectRelationNotFound,
    SelfReferencingKnowledgeObjectRelation,
)

__all__ = [
    "CrossOrganizationKnowledgeObjectRelation",
    "DuplicateKnowledgeObject",
    "DuplicateKnowledgeObjectRelation",
    "InvalidKnowledgeObjectStateTransition",
    "KnowledgeObjectAlreadyActive",
    "KnowledgeObjectAlreadyArchived",
    "KnowledgeObjectAlreadyDeleted",
    "KnowledgeObjectError",
    "KnowledgeObjectNotFound",
    "KnowledgeObjectRelationError",
    "KnowledgeObjectRelationNotFound",
    "KnowledgeObjectVersionConflict",
    "SafetyMainDomainError",
    "SelfReferencingKnowledgeObjectRelation",
]

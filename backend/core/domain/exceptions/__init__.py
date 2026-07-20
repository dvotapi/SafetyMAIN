from backend.core.domain.exceptions.base import SafetyMainDomainError
from backend.core.domain.exceptions.membership import (
    CannotActivateRevokedMembership,
    InactiveMembership,
    MembershipAlreadyActive,
    MembershipAlreadyRevoked,
    MembershipError,
    MembershipNotFound,
)
from backend.core.domain.exceptions.organization import (
    OrganizationError,
    OrganizationNotFound,
)
from backend.core.domain.exceptions.user import UserError, UserNotFound
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
    "CannotActivateRevokedMembership",
    "CrossOrganizationKnowledgeObjectRelation",
    "DuplicateKnowledgeObject",
    "DuplicateKnowledgeObjectRelation",
    "InactiveMembership",
    "InvalidKnowledgeObjectStateTransition",
    "KnowledgeObjectAlreadyActive",
    "KnowledgeObjectAlreadyArchived",
    "KnowledgeObjectAlreadyDeleted",
    "KnowledgeObjectError",
    "KnowledgeObjectNotFound",
    "KnowledgeObjectRelationError",
    "KnowledgeObjectRelationNotFound",
    "KnowledgeObjectVersionConflict",
    "MembershipAlreadyActive",
    "MembershipAlreadyRevoked",
    "MembershipError",
    "MembershipNotFound",
    "OrganizationError",
    "OrganizationNotFound",
    "SafetyMainDomainError",
    "UserError",
    "UserNotFound",
    "SelfReferencingKnowledgeObjectRelation",
]

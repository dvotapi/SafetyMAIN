from backend.core.infrastructure.persistence.sqlalchemy.repositories.knowledge_object_repository import (
    SQLAlchemyKnowledgeObjectRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories.knowledge_object_relation_repository import (
    SQLAlchemyKnowledgeObjectRelationRepository,
)

__all__ = [
    "SQLAlchemyKnowledgeObjectRelationRepository",
    "SQLAlchemyKnowledgeObjectRepository",
]

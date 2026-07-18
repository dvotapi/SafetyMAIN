from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base


class KnowledgeObjectRelationModel(Base):
    __tablename__ = "knowledge_object_relations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_object_id",
            "target_object_id",
            "relation_type",
            name="uq_knowledge_object_relations_directed",
        ),
        CheckConstraint(
            "source_object_id <> target_object_id",
            name="ck_knowledge_object_relations_no_self_reference",
        ),
        Index(
            "ix_knowledge_object_relations_outgoing",
            "organization_id",
            "source_object_id",
            "relation_type",
            "created_at",
            "relation_id",
        ),
        Index(
            "ix_knowledge_object_relations_incoming",
            "organization_id",
            "target_object_id",
            "relation_type",
            "created_at",
            "relation_id",
        ),
        Index(
            "ix_knowledge_object_relations_organization_id",
            "organization_id",
        ),
    )

    relation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
    )
    source_object_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_objects.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_object_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_objects.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(String(length=255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

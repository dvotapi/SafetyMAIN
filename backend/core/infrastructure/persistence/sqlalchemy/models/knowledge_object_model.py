from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base


class KnowledgeObjectModel(Base):
    __tablename__ = "knowledge_objects"
    __table_args__ = (
        Index("ix_knowledge_objects_organization_id", "organization_id"),
        Index("ix_knowledge_objects_object_type", "object_type"),
        Index("ix_knowledge_objects_status", "status"),
        Index(
            "ix_knowledge_objects_search_order",
            "organization_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
    )
    object_type: Mapped[str] = mapped_column(String(length=255), nullable=False)
    status: Mapped[str] = mapped_column(String(length=64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

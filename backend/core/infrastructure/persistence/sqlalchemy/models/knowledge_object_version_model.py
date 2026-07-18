from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base


class KnowledgeObjectVersionModel(Base):
    __tablename__ = "knowledge_object_versions"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_object_id",
            "version",
            name="uq_knowledge_object_versions_object_version",
        ),
        Index(
            "ix_knowledge_object_versions_history_order",
            "knowledge_object_id",
            "version",
        ),
        Index(
            "ix_knowledge_object_versions_organization_id",
            "organization_id",
        ),
    )

    history_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    knowledge_object_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("knowledge_objects.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

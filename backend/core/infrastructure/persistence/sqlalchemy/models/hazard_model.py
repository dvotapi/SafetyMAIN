from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base

_HAZARD_STATUSES = (
    "draft",
    "active",
    "archived",
)

_HAZARD_CATEGORIES = (
    "physical",
    "mechanical",
    "electrical",
    "chemical",
    "biological",
    "ergonomic",
    "psychosocial",
    "fire_and_explosion",
    "thermal",
    "radiation",
    "pressure",
    "work_at_height",
    "confined_space",
    "transport",
    "environmental",
    "dangerous_goods",
    "process_safety",
    "natural_hazard",
    "organizational",
    "other",
)


class HazardModel(Base):
    __tablename__ = "safety_hazards"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_safety_hazards_organization_id_code",
        ),
        CheckConstraint("btrim(title) <> ''", name="ck_safety_hazards_title_nonempty"),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in _HAZARD_STATUSES) + ")",
            name="ck_safety_hazards_status",
        ),
        CheckConstraint(
            "category IN (" + ", ".join(f"'{c}'" for c in _HAZARD_CATEGORIES) + ")",
            name="ck_safety_hazards_category",
        ),
        CheckConstraint("version >= 1", name="ck_safety_hazards_version_positive"),
        Index("ix_safety_hazards_organization_id", "organization_id"),
        Index("ix_safety_hazards_organization_id_status", "organization_id", "status"),
        Index(
            "ix_safety_hazards_organization_id_category",
            "organization_id",
            "category",
        ),
        Index(
            "ix_safety_hazards_organization_id_created_at",
            "organization_id",
            "created_at",
        ),
        Index(
            "ix_safety_hazards_organization_id_identified_at",
            "organization_id",
            "identified_at",
        ),
        Index(
            "ix_safety_hazards_safety_directions",
            "safety_directions",
            postgresql_using="gin",
        ),
        Index(
            "ix_safety_hazards_affected_subjects",
            "affected_subjects",
            postgresql_using="gin",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(length=64), nullable=False)
    title: Mapped[str] = mapped_column(String(length=512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    category: Mapped[str] = mapped_column(String(length=64), nullable=False)
    safety_directions: Mapped[list[str]] = mapped_column(
        ARRAY(String(length=64)),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(length=64), nullable=False)
    affected_subjects: Mapped[list[str]] = mapped_column(
        ARRAY(String(length=64)),
        nullable=False,
        server_default=text("'{}'"),
    )
    location_reference: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    process_reference: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    equipment_reference: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    extension_references: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    identified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    identified_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

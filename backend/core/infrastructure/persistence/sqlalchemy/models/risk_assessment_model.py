from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base

_STATUSES = (
    "draft",
    "under_review",
    "approved",
    "superseded",
    "archived",
)


class RiskAssessmentModel(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_risk_assessments_organization_id_code",
        ),
        CheckConstraint(
            "btrim(title) <> ''",
            name="ck_risk_assessments_title_nonempty",
        ),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in _STATUSES) + ")",
            name="ck_risk_assessments_status",
        ),
        CheckConstraint("version >= 1", name="ck_risk_assessments_version_positive"),
        Index("ix_risk_assessments_organization_id", "organization_id"),
        Index(
            "ix_risk_assessments_organization_id_status",
            "organization_id",
            "status",
        ),
        Index(
            "ix_risk_assessments_organization_id_hazard_id",
            "organization_id",
            "hazard_id",
        ),
        Index(
            "ix_risk_assessments_organization_id_profile",
            "organization_id",
            "assessment_profile",
        ),
        Index(
            "ix_risk_assessments_organization_id_created_at",
            "organization_id",
            "created_at",
        ),
        Index(
            "ix_risk_assessments_active_scope",
            "organization_id",
            "hazard_id",
            "assessment_profile",
            "assessed_object_type",
            "assessed_object_reference",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    hazard_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("safety_hazards.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(length=64), nullable=False)
    title: Mapped[str] = mapped_column(String(length=512), nullable=False)
    assessment_profile: Mapped[str] = mapped_column(String(length=64), nullable=False)
    assessed_object_type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    assessed_object_reference: Mapped[str] = mapped_column(
        String(length=256),
        nullable=False,
    )
    assessor_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assessment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    review_schedule: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    inherent_risk: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    residual_risk: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    controls: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    acceptance: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    competency_requirements: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    extension_references: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    archived_by: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

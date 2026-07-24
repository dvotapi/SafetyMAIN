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
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base

_STATUSES = (
    "draft",
    "planned",
    "in_implementation",
    "implemented",
    "verified_effective",
    "verified_ineffective",
    "suspended",
    "superseded",
    "archived",
    "cancelled",
)


class RiskControlModel(Base):
    __tablename__ = "risk_controls"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "code",
            name="uq_risk_controls_organization_id_code",
        ),
        Index(
            "uq_risk_controls_org_assessment_source_ref",
            "organization_id",
            "risk_assessment_id",
            "source_control_reference",
            unique=True,
            postgresql_where=text(
                "source_control_reference IS NOT NULL AND risk_assessment_id IS NOT NULL"
            ),
        ),
        CheckConstraint(
            "btrim(title) <> ''",
            name="ck_risk_controls_title_nonempty",
        ),
        CheckConstraint(
            "lifecycle_status IN (" + ", ".join(f"'{s}'" for s in _STATUSES) + ")",
            name="ck_risk_controls_lifecycle_status",
        ),
        CheckConstraint("version >= 1", name="ck_risk_controls_version_positive"),
        Index("ix_risk_controls_organization_id", "organization_id"),
        Index(
            "ix_risk_controls_organization_id_lifecycle_status",
            "organization_id",
            "lifecycle_status",
        ),
        Index(
            "ix_risk_controls_organization_id_hazard_id",
            "organization_id",
            "hazard_id",
        ),
        Index(
            "ix_risk_controls_organization_id_risk_assessment_id",
            "organization_id",
            "risk_assessment_id",
        ),
        Index(
            "ix_risk_controls_organization_id_owner_reference",
            "organization_id",
            "owner_reference",
        ),
        Index(
            "ix_risk_controls_organization_id_next_review_date",
            "organization_id",
            "next_review_date",
        ),
        Index(
            "ix_risk_controls_organization_id_latest_effectiveness_result",
            "organization_id",
            "latest_effectiveness_result",
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
    description: Mapped[str] = mapped_column(Text, nullable=False)
    hierarchy_level: Mapped[str] = mapped_column(String(length=32), nullable=False)
    control_nature: Mapped[str] = mapped_column(String(length=32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(length=64), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(length=256), nullable=True)
    hazard_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("safety_hazards.id", ondelete="SET NULL"),
        nullable=True,
    )
    risk_assessment_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_control_reference: Mapped[str | None] = mapped_column(
        String(length=128),
        nullable=True,
    )
    source_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    scope: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    owner: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    owner_reference: Mapped[str | None] = mapped_column(String(length=256), nullable=True)
    owner_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    implementation: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    verifications: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    review_schedule: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    competency_requirements: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    related_entities: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    extension_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    lifecycle_status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    latest_effectiveness_result: Mapped[str | None] = mapped_column(
        String(length=32),
        nullable=True,
    )
    next_review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verification_method_requirement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("''"),
    )
    suspension: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status_before_suspension: Mapped[str | None] = mapped_column(
        String(length=32),
        nullable=True,
    )
    superseded_by_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    archive_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)

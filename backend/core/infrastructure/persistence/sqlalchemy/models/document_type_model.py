from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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

_SAFETY_DOMAINS = (
    "occupational",
    "industrial",
    "labour",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)
_SUBJECT_KINDS = ("organization", "employee", "asset")


class DocumentTypeModel(Base):
    __tablename__ = "document_types"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_document_types_organization_id_code"
        ),
        CheckConstraint(
            "safety_domain IN (" + ", ".join(f"'{v}'" for v in _SAFETY_DOMAINS) + ")",
            name="ck_document_types_safety_domain",
        ),
        CheckConstraint(
            "subject_kind IN (" + ", ".join(f"'{v}'" for v in _SUBJECT_KINDS) + ")",
            name="ck_document_types_subject_kind",
        ),
        CheckConstraint(
            "(review_period_months IS NULL OR review_period_months > 0) "
            "AND (validity_months IS NULL OR validity_months > 0) "
            "AND (periodicity_months IS NULL OR periodicity_months > 0)",
            name="ck_document_types_periods_positive",
        ),
        CheckConstraint(
            "(CASE WHEN review_period_months IS NOT NULL THEN 1 ELSE 0 END "
            "+ CASE WHEN validity_months IS NOT NULL THEN 1 ELSE 0 END "
            "+ CASE WHEN periodicity_months IS NOT NULL THEN 1 ELSE 0 END) <= 1",
            name="ck_document_types_single_period",
        ),
        CheckConstraint(
            "jsonb_typeof(warning_thresholds_days) = 'array' "
            "AND jsonb_array_length(warning_thresholds_days) > 0",
            name="ck_document_types_warning_thresholds",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(length=64), nullable=False)
    title_ru: Mapped[str] = mapped_column(Text, nullable=False)
    safety_domain: Mapped[str] = mapped_column(String(length=32), nullable=False)
    subject_kind: Mapped[str] = mapped_column(String(length=32), nullable=False)
    review_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validity_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    periodicity_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_thresholds_days: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_approval_order: Mapped[bool] = mapped_column(Boolean, nullable=False)
    legal_basis: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''")
    )
    legal_basis_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

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
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base

# Mirrors migration 0015_document_shelf.
_SAFETY_DOMAINS = (
    "occupational",
    "industrial",
    "transport_security",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)
_KEPT_ON = ("organization", "facility", "event", "employee", "asset", "profession")
_OBLIGATION_LEVELS = ("mandatory", "conditional", "recommended")
_CURATED_STATUSES = (
    "present",
    "present_needs_review",
    "in_progress",
    "missing",
    "to_clarify",
)
_EXCLUSION_REASONS = ("not_applicable", "condition_not_met", "duplicate", "other")
_CONFIDENCE = ("verified", "secondary", "unconfirmed", "none")
_EXCLUSION_COLUMNS = (
    "exclusion_reason",
    "exclusion_comment",
    "exclusion_status_before",
    "excluded_by",
    "excluded_at",
)


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def _all_or_none(columns: tuple[str, ...]) -> str:
    all_null = " AND ".join(f"{c} IS NULL" for c in columns)
    all_set = " AND ".join(f"{c} IS NOT NULL" for c in columns)
    return f"({all_null}) OR ({all_set})"


def _uuid_fk(target: str, ondelete: str, *, nullable: bool = False) -> Mapped[UUID]:
    return mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(target, ondelete=ondelete),
        nullable=nullable,
    )


def _text() -> Mapped[str]:
    return mapped_column(Text, nullable=False, server_default=text("''"))


class ShelfSectionModel(Base):
    __tablename__ = "shelf_sections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_shelf_sections_organization_id_code"
        ),
        UniqueConstraint(
            "organization_id", "number", name="uq_shelf_sections_organization_id_number"
        ),
        CheckConstraint(
            _in_list("safety_domain", _SAFETY_DOMAINS),
            name="ck_shelf_sections_safety_domain",
        ),
        CheckConstraint("number BETWEEN 1 AND 99", name="ck_shelf_sections_number_range"),
        CheckConstraint("version > 0", name="ck_shelf_sections_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = _uuid_fk("organizations.id", "CASCADE")
    code: Mapped[str] = mapped_column(String(length=16), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    safety_domain: Mapped[str] = mapped_column(String(length=32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class ShelfSubsectionModel(Base):
    __tablename__ = "shelf_subsections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_shelf_subsections_organization_id_code"
        ),
        UniqueConstraint(
            "section_id", "position", name="uq_shelf_subsections_section_id_position"
        ),
        CheckConstraint("position >= 0", name="ck_shelf_subsections_position_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = _uuid_fk("organizations.id", "CASCADE")
    section_id: Mapped[UUID] = _uuid_fk("shelf_sections.id", "RESTRICT")
    code: Mapped[str] = mapped_column(String(length=16), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)


class ShelfSlotModel(Base):
    __tablename__ = "shelf_slots"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_shelf_slots_organization_id_code"),
        CheckConstraint(_in_list("kept_on", _KEPT_ON), name="ck_shelf_slots_kept_on"),
        CheckConstraint(
            _in_list("obligation_level", _OBLIGATION_LEVELS),
            name="ck_shelf_slots_obligation_level",
        ),
        CheckConstraint(
            _in_list("curated_status", _CURATED_STATUSES),
            name="ck_shelf_slots_curated_status",
        ),
        CheckConstraint(
            _in_list("basis_confidence", _CONFIDENCE), name="ck_shelf_slots_basis_confidence"
        ),
        CheckConstraint(
            "exclusion_reason IS NULL OR " + _in_list("exclusion_reason", _EXCLUSION_REASONS),
            name="ck_shelf_slots_exclusion_reason",
        ),
        CheckConstraint(
            "exclusion_status_before IS NULL OR "
            + _in_list("exclusion_status_before", _CURATED_STATUSES),
            name="ck_shelf_slots_exclusion_status_before",
        ),
        CheckConstraint(
            _all_or_none(_EXCLUSION_COLUMNS), name="ck_shelf_slots_exclusion_complete"
        ),
        CheckConstraint(
            "exclusion_comment IS NULL "
            "OR char_length(btrim(exclusion_comment)) BETWEEN 5 AND 1000",
            name="ck_shelf_slots_exclusion_comment_length",
        ),
        CheckConstraint(
            "obligation_level <> 'conditional' OR applicability_condition <> ''",
            name="ck_shelf_slots_condition_required",
        ),
        CheckConstraint(
            "char_length(title) BETWEEN 1 AND 500", name="ck_shelf_slots_title_length"
        ),
        CheckConstraint(
            "char_length(short_title) >= 1", name="ck_shelf_slots_short_title_nonempty"
        ),
        CheckConstraint(
            "review_period_months IS NULL OR review_period_months > 0",
            name="ck_shelf_slots_review_period_positive",
        ),
        CheckConstraint("version > 0", name="ck_shelf_slots_version_positive"),
        Index("ix_shelf_slots_organization_id_section_id", "organization_id", "section_id"),
        Index(
            "ix_shelf_slots_organization_id_subsection_id", "organization_id", "subsection_id"
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    organization_id: Mapped[UUID] = _uuid_fk("organizations.id", "CASCADE")
    code: Mapped[str] = mapped_column(String(length=32), nullable=False)
    section_id: Mapped[UUID] = _uuid_fk("shelf_sections.id", "RESTRICT")
    subsection_id: Mapped[UUID] = _uuid_fk("shelf_subsections.id", "RESTRICT")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    short_title: Mapped[str] = mapped_column(String(length=40), nullable=False)
    document_kind: Mapped[str] = mapped_column(String(length=64), nullable=False)
    kept_on: Mapped[str] = mapped_column(String(length=32), nullable=False)
    obligation_level: Mapped[str] = mapped_column(String(length=32), nullable=False)
    applicability_condition: Mapped[str] = _text()
    basis_regulation: Mapped[str] = _text()
    basis_clause: Mapped[str] = _text()
    basis_quote: Mapped[str] = _text()
    basis_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    basis_confidence: Mapped[str] = mapped_column(String(length=16), nullable=False)
    review_cycle_text: Mapped[str] = _text()
    review_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    curated_status: Mapped[str] = mapped_column(String(length=32), nullable=False)
    document_type_code: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    proposed_document_type: Mapped[str] = _text()
    responsible_text: Mapped[str] = _text()
    legacy_location: Mapped[str] = _text()
    notes: Mapped[str] = _text()
    package_code: Mapped[str] = _text()
    legacy_code: Mapped[str] = _text()
    exclusion_reason: Mapped[str | None] = mapped_column(String(length=32), nullable=True)
    exclusion_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusion_status_before: Mapped[str | None] = mapped_column(
        String(length=32), nullable=True
    )
    excluded_by: Mapped[UUID | None] = _uuid_fk("users.id", "RESTRICT", nullable=True)
    excluded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    import_fingerprint: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    last_imported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[UUID] = _uuid_fk("users.id", "RESTRICT")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[UUID] = _uuid_fk("users.id", "RESTRICT")
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class ShelfSlotDocumentModel(Base):
    """Link between a place and a compliance document; ``position`` keeps link order."""

    __tablename__ = "shelf_slot_documents"
    __table_args__ = (
        UniqueConstraint(
            "slot_id", "position", name="uq_shelf_slot_documents_slot_id_position"
        ),
        CheckConstraint(
            "position >= 0", name="ck_shelf_slot_documents_position_nonnegative"
        ),
        Index(
            "ix_shelf_slot_documents_organization_id_document_id",
            "organization_id",
            "document_id",
        ),
    )

    organization_id: Mapped[UUID] = _uuid_fk("organizations.id", "CASCADE")
    slot_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("shelf_slots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("compliance_documents.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    linked_by: Mapped[UUID] = _uuid_fk("users.id", "RESTRICT")

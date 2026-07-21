from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base


class AuditEventModel(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_occurred_at", "occurred_at"),
        Index("ix_audit_events_actor_user_id", "actor_user_id"),
        Index("ix_audit_events_authorization_organization_id", "authorization_organization_id"),
        Index("ix_audit_events_target_organization_id", "target_organization_id"),
        Index("ix_audit_events_action", "action"),
        Index("ix_audit_events_resource_type_resource_id", "resource_type", "resource_id"),
        Index("ix_audit_events_outcome", "outcome"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    authorization_organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    target_organization_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(length=64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(length=32), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )
    outcome: Mapped[str] = mapped_column(String(length=16), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

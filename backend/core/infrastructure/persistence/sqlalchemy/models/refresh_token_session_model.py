from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.infrastructure.persistence.sqlalchemy.base import Base


class RefreshTokenSessionModel(Base):
    __tablename__ = "refresh_token_sessions"
    __table_args__ = (
        UniqueConstraint("family_id", name="uq_refresh_token_sessions_family_id"),
        UniqueConstraint(
            "current_token_id_hash",
            name="uq_refresh_token_sessions_current_token_hash",
        ),
        CheckConstraint(
            "revocation_reason IS NULL OR revocation_reason IN ("
            "'logout', 'token_reuse_detected', 'user_deactivated', "
            "'administrative_revocation', 'session_expired', 'security_response'"
            ")",
            name="ck_refresh_token_sessions_reason",
        ),
        CheckConstraint(
            "(revoked_at IS NULL AND revocation_reason IS NULL) OR "
            "(revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)",
            name="ck_refresh_token_sessions_revocation_pair",
        ),
        Index("ix_refresh_token_sessions_user_id", "user_id"),
        Index(
            "ix_refresh_token_sessions_user_id_revoked_at",
            "user_id",
            "revoked_at",
        ),
        Index("ix_refresh_token_sessions_expires_at", "expires_at"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
    )
    current_token_id_hash: Mapped[str] = mapped_column(String(length=64), nullable=False)
    previous_token_id_hash: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(length=64), nullable=True)

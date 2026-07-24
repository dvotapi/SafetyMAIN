"""Create persistent refresh-token session storage.

Indexes:
- user_id: revoke-all-for-user and operational listings
- (user_id, revoked_at): active-session filtering for a user
- expires_at: retention cleanup scans
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_refresh_token_sessions"
down_revision = "0008_membership_role_check"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_token_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_token_id_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_token_id_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("family_id", name="uq_refresh_token_sessions_family_id"),
        sa.UniqueConstraint(
            "current_token_id_hash",
            name="uq_refresh_token_sessions_current_token_hash",
        ),
        sa.CheckConstraint(
            "revocation_reason IS NULL OR revocation_reason IN ("
            "'logout', 'token_reuse_detected', 'user_deactivated', "
            "'administrative_revocation', 'session_expired', 'security_response'"
            ")",
            name="ck_refresh_token_sessions_reason",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND revocation_reason IS NULL) OR "
            "(revoked_at IS NOT NULL AND revocation_reason IS NOT NULL)",
            name="ck_refresh_token_sessions_revocation_pair",
        ),
    )
    op.create_index(
        "ix_refresh_token_sessions_user_id",
        "refresh_token_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_refresh_token_sessions_user_id_revoked_at",
        "refresh_token_sessions",
        ["user_id", "revoked_at"],
    )
    op.create_index(
        "ix_refresh_token_sessions_expires_at",
        "refresh_token_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_refresh_token_sessions_expires_at",
        table_name="refresh_token_sessions",
    )
    op.drop_index(
        "ix_refresh_token_sessions_user_id_revoked_at",
        table_name="refresh_token_sessions",
    )
    op.drop_index(
        "ix_refresh_token_sessions_user_id",
        table_name="refresh_token_sessions",
    )
    op.drop_table("refresh_token_sessions")

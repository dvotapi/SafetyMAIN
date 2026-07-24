"""Add investigation-oriented indexes for audit_events.

Rationale:
- Tenant-scoped list queries always constrain by authorization/target organization and
  sort/filter by occurred_at; composite indexes support that access path.
- Action filters are common for taxonomy event-name / category expansion; pairing action
  with occurred_at supports investigation timelines.
- Request ID lives in JSONB metadata; an expression index supports exact correlation
  lookups without a schema column change.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_audit_investigation_indexes"
down_revision = "0005_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_audit_events_auth_org_occurred_at",
        "audit_events",
        ["authorization_organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_audit_events_target_org_occurred_at",
        "audit_events",
        ["target_organization_id", "occurred_at"],
    )
    op.create_index(
        "ix_audit_events_action_occurred_at",
        "audit_events",
        ["action", "occurred_at"],
    )
    op.create_index(
        "ix_audit_events_actor_occurred_at",
        "audit_events",
        ["actor_user_id", "occurred_at"],
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_audit_events_metadata_request_id "
            "ON audit_events ((metadata ->> 'request_id')) "
            "WHERE metadata ? 'request_id'"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_audit_events_metadata_request_id"))
    op.drop_index("ix_audit_events_actor_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_action_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_target_org_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_auth_org_occurred_at", table_name="audit_events")

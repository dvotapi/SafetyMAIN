from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003_organization_active_state"
down_revision = "0002_identity_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "uq_organizations_name_normalized",
        "organizations",
        [sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_organizations_name_normalized", table_name="organizations")
    op.drop_column("organizations", "is_active")

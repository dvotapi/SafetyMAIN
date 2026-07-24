"""Enforce canonical membership role values at the database level.

Invalid legacy role values fail the migration with a clear diagnostic rather
than being silently rewritten or deleted.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_membership_role_check"
down_revision = "0007_audit_event_integrity_chain"
branch_labels = None
depends_on = None

_ALLOWED_ROLES = ("admin", "member", "auditor")


def upgrade() -> None:
    connection = op.get_bind()
    invalid_roles = connection.execute(
        sa.text(
            """
            SELECT DISTINCT role
            FROM memberships
            WHERE role IS NULL
               OR role NOT IN ('admin', 'member', 'auditor')
            ORDER BY 1
            """
        )
    ).scalars().all()
    if invalid_roles:
        rendered = ", ".join(repr(role) for role in invalid_roles)
        raise RuntimeError(
            "Cannot apply ck_memberships_role_system: memberships contain "
            f"unsupported role values: {rendered}. Repair those rows before "
            "upgrading. Allowed values: "
            + ", ".join(_ALLOWED_ROLES)
            + "."
        )

    op.create_check_constraint(
        "ck_memberships_role_system",
        "memberships",
        "role IN ('admin', 'member', 'auditor')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_memberships_role_system", "memberships", type_="check")

"""Document file role: working file or signed scan (TASK-P11-012 phase 4, D1).

Revision ID: 0016_document_file_role
Revises: 0015_document_shelf
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0016_document_file_role"
down_revision = "0015_document_shelf"
branch_labels = None
depends_on = None

_ROLES = ("working", "signed_scan")


def upgrade() -> None:
    op.add_column(
        "document_files",
        sa.Column(
            "role",
            sa.String(length=16),
            nullable=False,
            server_default="working",
        ),
    )
    op.create_check_constraint(
        "ck_document_files_role",
        "document_files",
        "role IN (" + ", ".join(f"'{role}'" for role in _ROLES) + ")",
    )


def downgrade() -> None:
    op.drop_constraint("ck_document_files_role", "document_files", type_="check")
    op.drop_column("document_files", "role")

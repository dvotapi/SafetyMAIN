"""Replace safety domain `labour` with `transport_security` (TASK-P11-012 phase 1).

«ТрБез» means transport security (16-ФЗ, ПП РФ № 1640); `labour` was a
mistranslation introduced in 0013.
"""

from __future__ import annotations

from alembic import op

revision = "0014_transport_security_domain"
down_revision = "0013_compliance_documents"
branch_labels = None
depends_on = None

_CONSTRAINT = "ck_document_types_safety_domain"
_TABLE = "document_types"

# Literal lists: migrations must not depend on application code that changes later.
_SAFETY_DOMAINS_0013 = (
    "occupational",
    "industrial",
    "labour",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)
_SAFETY_DOMAINS_0014 = (
    "occupational",
    "industrial",
    "transport_security",
    "fire",
    "environmental",
    "road",
    "dangerous_goods",
)


def _in_list(values: tuple[str, ...]) -> str:
    return "safety_domain IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def _replace_domain(old: str, new: str, allowed: tuple[str, ...]) -> None:
    # The existing constraint rejects `new`, so the update runs between drop and create.
    op.drop_constraint(_CONSTRAINT, _TABLE, type_="check")
    op.execute(
        f"UPDATE {_TABLE} SET safety_domain = '{new}' WHERE safety_domain = '{old}'"
    )
    op.create_check_constraint(_CONSTRAINT, _TABLE, _in_list(allowed))


def upgrade() -> None:
    _replace_domain("labour", "transport_security", _SAFETY_DOMAINS_0014)


def downgrade() -> None:
    _replace_domain("transport_security", "labour", _SAFETY_DOMAINS_0013)

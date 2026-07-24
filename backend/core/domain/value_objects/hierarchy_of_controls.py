from __future__ import annotations

from backend.core.domain.value_objects.safety_enums import ControlType

# Preferred order for Hierarchy of Controls (most effective first).
HIERARCHY_OF_CONTROLS: tuple[ControlType, ...] = (
    ControlType.ELIMINATION,
    ControlType.SUBSTITUTION,
    ControlType.ENGINEERING,
    ControlType.ADMINISTRATIVE,
    ControlType.PPE,
)


def is_preferred_over(left: ControlType, right: ControlType) -> bool:
    """Return True when left is higher on the hierarchy than right."""

    return left.hierarchy_rank < right.hierarchy_rank

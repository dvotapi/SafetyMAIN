from __future__ import annotations

from collections.abc import Mapping

from backend.core.domain.exceptions.safety import InvalidSafetyLifecycleTransition


def transition(
    *,
    aggregate: str,
    current: str,
    target: str,
    allowed: Mapping[str, frozenset[str]],
) -> None:
    permitted = allowed.get(current, frozenset())
    if target not in permitted:
        raise InvalidSafetyLifecycleTransition(
            aggregate=aggregate,
            source=current,
            target=target,
        )

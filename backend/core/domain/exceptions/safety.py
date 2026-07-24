from __future__ import annotations

from backend.core.domain.exceptions.base import SafetyMainDomainError


class SafetyDomainError(SafetyMainDomainError):
    """Base error for Safety domain invariants."""


class InvalidSafetyLifecycleTransition(SafetyDomainError):
    def __init__(self, *, aggregate: str, source: str, target: str) -> None:
        self.aggregate = aggregate
        self.source = source
        self.target = target
        super().__init__(
            f"Invalid {aggregate} lifecycle transition: {source} -> {target}."
        )

from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.hazard import Hazard
from backend.core.domain.value_objects import OrganizationId
from backend.core.domain.value_objects.hazard_code import HazardCode
from backend.core.domain.value_objects.hazard_query import HazardPage, HazardQuery
from backend.core.domain.value_objects.safety_ids import HazardId


class HazardRepositoryContract(Protocol):
    """Organization-scoped hazard persistence contract.

    Implementations must never expose unscoped reads by hazard id alone.
    Repositories must not commit transactions.
    """

    def add(self, hazard: Hazard) -> None:
        ...

    def get(
        self,
        organization_id: OrganizationId,
        hazard_id: HazardId,
    ) -> Hazard | None:
        ...

    def get_by_code(
        self,
        organization_id: OrganizationId,
        code: HazardCode,
    ) -> Hazard | None:
        ...

    def list(self, query: HazardQuery) -> HazardPage:
        ...

    def save(self, hazard: Hazard, *, expected_version: int) -> None:
        ...

from __future__ import annotations

from typing import Protocol

from backend.core.domain.entities.incident import Incident
from backend.core.domain.value_objects.safety_ids import IncidentId


class IncidentRepositoryContract(Protocol):
    def add(self, incident: Incident) -> None:
        ...

    def get(self, incident_id: IncidentId) -> Incident:
        ...

    def save(self, incident: Incident) -> None:
        ...

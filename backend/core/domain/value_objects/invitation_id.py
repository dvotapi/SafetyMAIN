from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvitationId(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: UUID

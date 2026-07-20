from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field


class APIValidationViolation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    location: tuple[str, ...]
    message: str
    type: str


class APIValidationErrorDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    violations: tuple[APIValidationViolation, ...] = ()


class APIErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    details: Mapping[str, object] | None = None


class APIErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: APIErrorDetail = Field(...)

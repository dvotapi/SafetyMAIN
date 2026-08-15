from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthSessionUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    email: str
    display_name: str
    status: str


class AuthSessionMembership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    organization_name: str
    role: str
    status: str
    permissions: list[str]


class AuthSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: AuthSessionUser
    memberships: list[AuthSessionMembership]

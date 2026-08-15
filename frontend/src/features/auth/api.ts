import { apiClient } from "@/services/api/client";
import type {
  AuthMembership,
  AuthSession,
  AuthUser,
  TokenPair,
} from "@/features/auth/types";

interface TokenResponseDto {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface SessionResponseDto {
  user: {
    id: string;
    email: string;
    display_name: string;
    status: string;
  };
  memberships: Array<{
    organization_id: string;
    organization_name: string;
    role: string;
    status: string;
    permissions: string[];
  }>;
}

export function toTokenPair(dto: TokenResponseDto): TokenPair {
  return {
    accessToken: dto.access_token,
    refreshToken: dto.refresh_token,
    tokenType: dto.token_type,
    expiresAt: Date.now() + dto.expires_in * 1000,
  };
}

function mapSession(dto: SessionResponseDto): AuthSession {
  const user: AuthUser = {
    id: dto.user.id,
    email: dto.user.email,
    displayName: dto.user.display_name,
    status: dto.user.status,
  };
  const memberships: AuthMembership[] = dto.memberships.map((m) => ({
    organizationId: m.organization_id,
    organizationName: m.organization_name,
    role: m.role,
    status: m.status,
    permissions: m.permissions,
  }));
  return { user, memberships };
}

export async function loginRequest(
  email: string,
  password: string,
): Promise<TokenPair> {
  const dto = await apiClient.request<TokenResponseDto>({
    method: "POST",
    path: "/api/v1/auth/login",
    body: { email, password },
  });
  if (!dto) {
    throw new Error("Empty login response");
  }
  return toTokenPair(dto);
}

export async function refreshRequest(refreshToken: string): Promise<TokenPair> {
  const dto = await apiClient.request<TokenResponseDto>({
    method: "POST",
    path: "/api/v1/auth/refresh",
    body: { refresh_token: refreshToken },
  });
  if (!dto) {
    throw new Error("Empty refresh response");
  }
  return toTokenPair(dto);
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  await apiClient.request<null>({
    method: "POST",
    path: "/api/v1/auth/logout",
    body: { refresh_token: refreshToken },
  });
}

export async function fetchSession(accessToken: string): Promise<AuthSession> {
  const dto = await apiClient.request<SessionResponseDto>({
    method: "GET",
    path: "/api/v1/auth/session",
    getAccessToken: async () => accessToken,
  });
  if (!dto) {
    throw new Error("Empty session response");
  }
  return mapSession(dto);
}

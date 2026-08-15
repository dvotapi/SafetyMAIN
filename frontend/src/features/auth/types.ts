export type AuthStatus =
  | "unauthenticated"
  | "authenticating"
  | "authenticated"
  | "restoring"
  | "refreshing"
  | "expired";

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresAt: number; // epoch ms
  tokenType: string;
}

export interface AuthUser {
  id: string;
  email: string;
  displayName: string;
  status: string;
}

export interface AuthMembership {
  organizationId: string;
  organizationName: string;
  role: string;
  status: string;
  permissions: string[];
}

export interface AuthSession {
  user: AuthUser;
  memberships: AuthMembership[];
}

export interface AuthState {
  status: AuthStatus;
  tokens: TokenPair | null;
  session: AuthSession | null;
  organizationId: string | null;
  error: string | null;
}

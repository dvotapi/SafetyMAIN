"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  fetchSession,
  loginRequest,
  logoutRequest,
  refreshRequest,
} from "@/features/auth/api";
import { authStorage } from "@/features/auth/storage";
import type {
  AuthMembership,
  AuthSession,
  AuthState,
  AuthStatus,
  AuthUser,
  TokenPair,
} from "@/features/auth/types";
import {
  bindAuthProviders,
  clearAuthProviders,
} from "@/services/api/auth-bridge";
import { toUserSafeMessage } from "@/services/api/errors";

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  currentMembership: AuthMembership | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const REFRESH_SKEW_MS = 60_000;

function pickOrganizationId(
  session: AuthSession,
  preferred: string | null,
): string | null {
  if (
    preferred &&
    session.memberships.some((m) => m.organizationId === preferred)
  ) {
    return preferred;
  }
  return session.memberships[0]?.organizationId ?? null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>("restoring");
  const [tokens, setTokens] = useState<TokenPair | null>(null);
  const [session, setSession] = useState<AuthSession | null>(null);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refreshInFlight = useRef<Promise<boolean> | null>(null);
  const tokensRef = useRef<TokenPair | null>(null);
  const organizationIdRef = useRef<string | null>(null);

  useEffect(() => {
    tokensRef.current = tokens;
  }, [tokens]);

  useEffect(() => {
    organizationIdRef.current = organizationId;
  }, [organizationId]);

  const applySession = useCallback(
    (nextTokens: TokenPair, nextSession: AuthSession) => {
      const orgId = pickOrganizationId(
        nextSession,
        authStorage.loadOrganizationId(),
      );
      authStorage.saveTokens(nextTokens);
      authStorage.saveOrganizationId(orgId);
      setTokens(nextTokens);
      setSession(nextSession);
      setOrganizationId(orgId);
      setStatus("authenticated");
      setError(null);
    },
    [],
  );

  const clearAuth = useCallback(() => {
    authStorage.clearAll();
    setTokens(null);
    setSession(null);
    setOrganizationId(null);
    setStatus("unauthenticated");
    queryClient.clear();
  }, [queryClient]);

  const refresh = useCallback(async (): Promise<boolean> => {
    if (refreshInFlight.current) {
      return refreshInFlight.current;
    }
    const current = tokensRef.current ?? authStorage.loadTokens();
    if (!current?.refreshToken) {
      clearAuth();
      setStatus("expired");
      return false;
    }

    const run = (async () => {
      setStatus("refreshing");
      try {
        const nextTokens = await refreshRequest(current.refreshToken);
        const nextSession = await fetchSession(nextTokens.accessToken);
        applySession(nextTokens, nextSession);
        return true;
      } catch {
        clearAuth();
        setStatus("expired");
        return false;
      } finally {
        refreshInFlight.current = null;
      }
    })();

    refreshInFlight.current = run;
    return run;
  }, [applySession, clearAuth]);

  const ensureFreshAccessToken = useCallback(async (): Promise<
    string | null
  > => {
    const current = tokensRef.current ?? authStorage.loadTokens();
    if (!current) {
      return null;
    }
    if (current.expiresAt - Date.now() > REFRESH_SKEW_MS) {
      return current.accessToken;
    }
    const ok = await refresh();
    return ok ? (tokensRef.current?.accessToken ?? null) : null;
  }, [refresh]);

  useEffect(() => {
    bindAuthProviders({
      getAccessToken: ensureFreshAccessToken,
      getOrganizationId: async () => organizationIdRef.current,
      onUnauthorized: async () => {
        const ok = await refresh();
        return ok;
      },
    });
    return () => clearAuthProviders();
  }, [ensureFreshAccessToken, refresh]);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      const stored = authStorage.loadTokens();
      if (!stored) {
        if (!cancelled) {
          setStatus("unauthenticated");
        }
        return;
      }
      setStatus("restoring");
      try {
        let pair = stored;
        if (pair.expiresAt - Date.now() <= REFRESH_SKEW_MS) {
          pair = await refreshRequest(pair.refreshToken);
        }
        const nextSession = await fetchSession(pair.accessToken);
        if (!cancelled) {
          applySession(pair, nextSession);
        }
      } catch {
        if (!cancelled) {
          clearAuth();
        }
      }
    }
    void restore();
    return () => {
      cancelled = true;
    };
  }, [applySession, clearAuth]);

  const login = useCallback(
    async (email: string, password: string) => {
      setStatus("authenticating");
      setError(null);
      try {
        const nextTokens = await loginRequest(email, password);
        const nextSession = await fetchSession(nextTokens.accessToken);
        applySession(nextTokens, nextSession);
      } catch (err) {
        clearAuth();
        setStatus("unauthenticated");
        setError(toUserSafeMessage(err));
        throw err;
      }
    },
    [applySession, clearAuth],
  );

  const logout = useCallback(async () => {
    const current = tokensRef.current;
    try {
      if (current?.refreshToken) {
        await logoutRequest(current.refreshToken);
      }
    } catch {
      // Logout is idempotent server-side; always clear locally.
    }
    clearAuth();
  }, [clearAuth]);

  const currentMembership = useMemo(() => {
    if (!session || !organizationId) {
      return null;
    }
    return (
      session.memberships.find((m) => m.organizationId === organizationId) ??
      null
    );
  }, [organizationId, session]);

  const hasPermission = useCallback(
    (permission: string) => {
      return Boolean(currentMembership?.permissions.includes(permission));
    },
    [currentMembership],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      tokens,
      session,
      organizationId,
      error,
      login,
      logout,
      refresh,
      hasPermission,
      currentMembership,
    }),
    [
      status,
      tokens,
      session,
      organizationId,
      error,
      login,
      logout,
      refresh,
      hasPermission,
      currentMembership,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export function useCurrentUser(): AuthUser | null {
  return useAuth().session?.user ?? null;
}

export function usePermissions(): {
  permissions: string[];
  hasPermission: (permission: string) => boolean;
} {
  const { currentMembership, hasPermission } = useAuth();
  return {
    permissions: currentMembership?.permissions ?? [],
    hasPermission,
  };
}

export function useOrganization(): {
  organizationId: string | null;
  organizationName: string | null;
  membership: AuthMembership | null;
} {
  const { organizationId, currentMembership } = useAuth();
  return {
    organizationId,
    organizationName: currentMembership?.organizationName ?? null,
    membership: currentMembership,
  };
}

export function useAuthenticated(): boolean {
  return useAuth().status === "authenticated";
}

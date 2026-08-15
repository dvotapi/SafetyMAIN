import type { TokenPair } from "@/features/auth/types";

const ACCESS_KEY = "safetymain.auth.access";
const REFRESH_KEY = "safetymain.auth.refresh";
const EXPIRES_KEY = "safetymain.auth.expires_at";
const TYPE_KEY = "safetymain.auth.token_type";
const ORG_KEY = "safetymain.auth.organization_id";

/**
 * Session storage (tab-scoped) — acceptable bootstrap persistence.
 * Prefer httpOnly cookies in a later hardening task.
 */
export const authStorage = {
  loadTokens(): TokenPair | null {
    if (typeof window === "undefined") {
      return null;
    }
    try {
      const accessToken = sessionStorage.getItem(ACCESS_KEY);
      const refreshToken = sessionStorage.getItem(REFRESH_KEY);
      const expiresRaw = sessionStorage.getItem(EXPIRES_KEY);
      const tokenType = sessionStorage.getItem(TYPE_KEY) ?? "bearer";
      if (!accessToken || !refreshToken || !expiresRaw) {
        return null;
      }
      return {
        accessToken,
        refreshToken,
        expiresAt: Number(expiresRaw),
        tokenType,
      };
    } catch {
      return null;
    }
  },

  saveTokens(tokens: TokenPair): void {
    sessionStorage.setItem(ACCESS_KEY, tokens.accessToken);
    sessionStorage.setItem(REFRESH_KEY, tokens.refreshToken);
    sessionStorage.setItem(EXPIRES_KEY, String(tokens.expiresAt));
    sessionStorage.setItem(TYPE_KEY, tokens.tokenType);
  },

  clearTokens(): void {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(EXPIRES_KEY);
    sessionStorage.removeItem(TYPE_KEY);
  },

  loadOrganizationId(): string | null {
    try {
      return sessionStorage.getItem(ORG_KEY);
    } catch {
      return null;
    }
  },

  saveOrganizationId(organizationId: string | null): void {
    if (organizationId) {
      sessionStorage.setItem(ORG_KEY, organizationId);
    } else {
      sessionStorage.removeItem(ORG_KEY);
    }
  },

  clearAll(): void {
    this.clearTokens();
    this.saveOrganizationId(null);
  },
};

import { beforeEach, describe, expect, it, vi } from "vitest";

import { authStorage } from "@/features/auth/storage";
import { toTokenPair } from "@/features/auth/api";

describe("auth storage", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("round-trips tokens", () => {
    const tokens = toTokenPair({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 3600,
    });
    authStorage.saveTokens(tokens);
    const loaded = authStorage.loadTokens();
    expect(loaded?.accessToken).toBe("a");
    expect(loaded?.refreshToken).toBe("r");
    authStorage.clearAll();
    expect(authStorage.loadTokens()).toBeNull();
  });
});

describe("toTokenPair", () => {
  it("computes expiry", () => {
    vi.spyOn(Date, "now").mockReturnValue(1_000_000);
    const pair = toTokenPair({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 10,
    });
    expect(pair.expiresAt).toBe(1_010_000);
  });
});

import { describe, expect, it } from "vitest";

import { filterNavigationByPermissions } from "@/lib/filter-navigation";
import { primaryNavigation } from "@/lib/navigation";

describe("filterNavigationByPermissions", () => {
  it("hides administration without user:read", () => {
    const filtered = filterNavigationByPermissions(
      primaryNavigation,
      (permission) => permission === "hazard:read",
    );
    expect(filtered.some((s) => s.id === "administration")).toBe(false);
    expect(filtered.some((s) => s.id === "safety")).toBe(true);
    expect(filtered.some((s) => s.id === "overview")).toBe(true);
  });

  it("shows administration for admins", () => {
    const filtered = filterNavigationByPermissions(
      primaryNavigation,
      () => true,
    );
    expect(filtered.some((s) => s.id === "administration")).toBe(true);
  });
});

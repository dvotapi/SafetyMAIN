import { describe, expect, it } from "vitest";

import { formatDateOnly, formatDateTime } from "@/utils/format-date";

describe("Russian date formatting", () => {
  it("uses Russian month names", () => {
    expect(formatDateOnly("2027-03-01T12:00:00Z")).toContain("мар");
    expect(formatDateTime("2027-03-01T12:00:00Z")).toContain("мар");
  });

  it("preserves empty and invalid values", () => {
    expect(formatDateOnly(null)).toBe("—");
    expect(formatDateTime("not-a-date")).toBe("not-a-date");
  });
});

import { describe, expect, it } from "vitest";

import { formatPluralRu } from "@/utils/format-plural";

describe("formatPluralRu", () => {
  it.each([
    [1, "запись"],
    [21, "запись"],
    [2, "записи"],
    [4, "записи"],
    [22, "записи"],
    [24, "записи"],
    [0, "записей"],
    [5, "записей"],
    [11, "записей"],
    [14, "записей"],
    [20, "записей"],
    [25, "записей"],
  ])("selects the correct form for %i", (count, expected) => {
    expect(formatPluralRu(count, "запись", "записи", "записей")).toBe(expected);
  });
});

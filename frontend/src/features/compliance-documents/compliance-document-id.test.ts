import { describe, expect, it } from "vitest";

import { assertComplianceDocumentId } from "@/features/compliance-documents/api/compliance-documents-id";

describe("assertComplianceDocumentId", () => {
  it("returns a well-formed UUID encoded", () => {
    const id = "11111111-1111-1111-1111-111111111111";
    expect(assertComplianceDocumentId(id)).toBe(id);
  });

  it("rejects path traversal and non-UUID input", () => {
    expect(() => assertComplianceDocumentId("..")).toThrow();
    expect(() => assertComplianceDocumentId("../../etc/passwd")).toThrow();
    expect(() =>
      assertComplianceDocumentId(
        "11111111-1111-1111-1111-111111111111/../other",
      ),
    ).toThrow();
    expect(() => assertComplianceDocumentId("")).toThrow();
    expect(() => assertComplianceDocumentId("not-a-uuid")).toThrow();
  });
});

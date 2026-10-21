import { describe, expect, it } from "vitest";

import {
  complianceDocumentStatusLabel,
  complianceDocumentStatusToVisual,
  shouldShowReviewDueWarning,
} from "@/features/compliance-documents/utils/status";

describe("complianceDocumentStatusToVisual", () => {
  it("maps every backend status to a visual", () => {
    expect(complianceDocumentStatusToVisual("draft")).toBe("draft");
    expect(complianceDocumentStatusToVisual("approved")).toBe("approved");
    expect(complianceDocumentStatusToVisual("active")).toBe("active");
    expect(complianceDocumentStatusToVisual("under_review")).toBe(
      "under_review",
    );
    expect(complianceDocumentStatusToVisual("superseded")).toBe("superseded");
    expect(complianceDocumentStatusToVisual("archived")).toBe("archived");
  });

  it("provides Russian labels for every status", () => {
    expect(complianceDocumentStatusLabel("draft")).toBe("Черновик");
    expect(complianceDocumentStatusLabel("active")).toBe("Действует");
    expect(complianceDocumentStatusLabel("archived")).toBe("Архив");
  });
});

describe("shouldShowReviewDueWarning", () => {
  it("shows warning only for in-force statuses", () => {
    expect(shouldShowReviewDueWarning("active", true)).toBe(true);
    expect(shouldShowReviewDueWarning("under_review", true)).toBe(true);
  });

  it("hides warning for terminal/non-active statuses", () => {
    expect(shouldShowReviewDueWarning("draft", true)).toBe(false);
    expect(shouldShowReviewDueWarning("approved", true)).toBe(false);
    expect(shouldShowReviewDueWarning("superseded", true)).toBe(false);
    expect(shouldShowReviewDueWarning("archived", true)).toBe(false);
  });

  it("hides warning when flag is false", () => {
    expect(shouldShowReviewDueWarning("active", false)).toBe(false);
  });
});

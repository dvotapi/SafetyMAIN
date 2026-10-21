import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComplianceDocumentStatusBadge } from "@/features/compliance-documents/components/compliance-document-status-badge";

describe("ComplianceDocumentStatusBadge", () => {
  it("renders the Russian label of the given status", () => {
    render(<ComplianceDocumentStatusBadge status="under_review" />);
    expect(screen.getByText("На пересмотре")).toBeInTheDocument();
  });

  it("renders every status without throwing", () => {
    for (const status of [
      "draft",
      "approved",
      "active",
      "under_review",
      "superseded",
      "archived",
    ] as const) {
      const { unmount } = render(
        <ComplianceDocumentStatusBadge status={status} />,
      );
      unmount();
    }
    expect(true).toBe(true);
  });
});

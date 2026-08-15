import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { HazardRelatedAssessments } from "@/features/hazards/components/hazard-related-assessments";
import type { RiskAssessmentSummary } from "@/features/hazards/types/hazard-types";

afterEach(() => {
  cleanup();
});

const assessments: RiskAssessmentSummary[] = [
  {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    code: "RA-1",
    title: "Machine guarding",
    status: "approved",
    assessmentProfile: "simple_3x3",
    inherentRiskLabel: "High",
    residualRiskLabel: "Medium",
    approvedAt: "2026-08-01T00:00:00Z",
    updatedAt: "2026-08-01T00:00:00Z",
  },
];

describe("HazardRelatedAssessments", () => {
  it("links related assessment rows to public risk assessment routes", () => {
    render(<HazardRelatedAssessments assessments={assessments} canView />);

    const links = screen.getAllByRole("link", {
      name: /RA-1|Machine guarding/,
    });
    expect(links.length).toBeGreaterThanOrEqual(2);
    for (const link of links) {
      expect(link).toHaveAttribute(
        "href",
        "/safety/risk-assessments/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      );
    }
  });
});

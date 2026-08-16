import { describe, expect, it } from "vitest";

import {
  effectivenessLabel,
  effectivenessToVisual,
  formatRiskControlEnumLabel,
  implementationStateLabel,
  riskControlStatusToVisual,
  VERIFIABLE_RESULTS,
} from "@/features/risk-controls/utils/risk-control-status";

describe("riskControlStatusToVisual", () => {
  it("maps every backend status to an existing VisualStatus", () => {
    expect(riskControlStatusToVisual("draft")).toBe("draft");
    expect(riskControlStatusToVisual("planned")).toBe("planned");
    expect(riskControlStatusToVisual("in_implementation")).toBe(
      "in_implementation",
    );
    expect(riskControlStatusToVisual("implemented")).toBe("implemented");
    expect(riskControlStatusToVisual("verified_effective")).toBe(
      "verified_effective",
    );
    expect(riskControlStatusToVisual("verified_ineffective")).toBe(
      "verified_ineffective",
    );
    expect(riskControlStatusToVisual("suspended")).toBe("suspended");
    expect(riskControlStatusToVisual("superseded")).toBe("superseded");
    expect(riskControlStatusToVisual("archived")).toBe("archived");
    expect(riskControlStatusToVisual("cancelled")).toBe("cancelled");
  });
});

describe("effectiveness", () => {
  it("keeps partially effective distinct from effective and ineffective", () => {
    expect(effectivenessToVisual("effective")).toBe("verified_effective");
    expect(effectivenessToVisual("partially_effective")).toBe(
      "verified_partially_effective",
    );
    expect(effectivenessToVisual("ineffective")).toBe("verified_ineffective");
    expect(effectivenessLabel("partially_effective")).toBe(
      "Verified Partially Effective",
    );
    expect(effectivenessLabel("effective")).toBe("Verified Effective");
    expect(effectivenessLabel("ineffective")).toBe("Verified Ineffective");
  });

  it("renders no verification as an explicit label, not a blank", () => {
    expect(effectivenessLabel(null)).toBe("Not verified");
    expect(effectivenessToVisual(null)).toBeNull();
  });

  it("offers only the three domain-accepted results for recording", () => {
    expect(VERIFIABLE_RESULTS).toEqual([
      "effective",
      "partially_effective",
      "ineffective",
    ]);
  });
});

describe("implementationStateLabel", () => {
  it("describes implementation independently of lifecycle status", () => {
    expect(
      implementationStateLabel({
        status: "draft",
        progress: 0,
        actualCompletionDate: null,
      }),
    ).toBe("Not planned");
    expect(
      implementationStateLabel({
        status: "planned",
        progress: 0,
        actualCompletionDate: null,
      }),
    ).toBe("Planned");
    expect(
      implementationStateLabel({
        status: "in_implementation",
        progress: 40,
        actualCompletionDate: null,
      }),
    ).toBe("In progress — 40%");
    expect(
      implementationStateLabel({
        status: "implemented",
        progress: 100,
        actualCompletionDate: "2026-08-01T00:00:00Z",
      }),
    ).toBe("Implemented");
  });
});

describe("formatRiskControlEnumLabel", () => {
  it("title-cases snake_case values", () => {
    expect(formatRiskControlEnumLabel("organizational_unit")).toBe(
      "Organizational Unit",
    );
  });
});

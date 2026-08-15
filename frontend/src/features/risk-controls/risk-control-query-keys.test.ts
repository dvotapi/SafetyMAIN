import { describe, expect, it } from "vitest";

import { riskControlKeys } from "@/features/risk-controls/api/risk-control-query-keys";

const ORG = "22222222-2222-2222-2222-222222222222";

describe("riskControlKeys", () => {
  it("scopes every key by organization so caches cannot cross tenants", () => {
    expect(riskControlKeys.all(ORG)).toEqual(["risk-controls", ORG]);
    expect(riskControlKeys.all(null)).toEqual(["risk-controls", "none"]);
    expect(riskControlKeys.all("other-org")).not.toEqual(riskControlKeys.all(ORG));
  });

  it("nests lists and details under the org root", () => {
    expect(riskControlKeys.lists(ORG)).toEqual(["risk-controls", ORG, "list"]);
    expect(riskControlKeys.detail(ORG, "rc-1")).toEqual([
      "risk-controls",
      ORG,
      "detail",
      "rc-1",
    ]);
    expect(riskControlKeys.activity(ORG, "rc-1")).toEqual([
      "risk-controls",
      ORG,
      "detail",
      "rc-1",
      "activity",
    ]);
  });

  it("keeps list keys stable for equal filters", () => {
    const filters = { limit: 25, offset: 0, search: "guard" };
    expect(riskControlKeys.list(ORG, filters)).toEqual(
      riskControlKeys.list(ORG, { ...filters }),
    );
  });

  it("separates assessment-scoped and hazard-scoped lists", () => {
    expect(riskControlKeys.forAssessment(ORG, "ra-1")).toEqual([
      "risk-controls",
      ORG,
      "list",
      "for-assessment",
      "ra-1",
    ]);
    expect(riskControlKeys.forHazard(ORG, "hz-1")).toEqual([
      "risk-controls",
      ORG,
      "list",
      "for-hazard",
      "hz-1",
    ]);
  });
});

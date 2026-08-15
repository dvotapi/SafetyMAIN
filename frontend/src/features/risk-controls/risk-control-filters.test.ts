import { describe, expect, it } from "vitest";

import {
  DEFAULT_RISK_CONTROL_REGISTRY_STATE,
  hasActiveRiskControlRegistryFilters,
  parseRiskControlRegistrySearchParams,
  registryStateToListParams,
  serializeRiskControlRegistrySearchParams,
} from "@/features/risk-controls/utils/risk-control-filters";

function parse(qs: string) {
  return parseRiskControlRegistrySearchParams(new URLSearchParams(qs));
}

describe("parseRiskControlRegistrySearchParams", () => {
  it("returns defaults for an empty query string", () => {
    expect(parse("")).toEqual(DEFAULT_RISK_CONTROL_REGISTRY_STATE);
  });

  it("drops unknown enum values instead of forwarding them to the API", () => {
    expect(parse("status=bogus").status).toBe("");
    expect(parse("hierarchyLevel=bogus").hierarchyLevel).toBe("");
    expect(parse("effectiveness=bogus").effectiveness).toBe("");
  });

  it("accepts known enum values", () => {
    expect(parse("status=implemented").status).toBe("implemented");
    expect(parse("hierarchyLevel=engineering").hierarchyLevel).toBe(
      "engineering",
    );
    expect(parse("effectiveness=partially_effective").effectiveness).toBe(
      "partially_effective",
    );
  });

  it("clamps page and page size", () => {
    expect(parse("page=0").page).toBe(1);
    expect(parse("page=-3").page).toBe(1);
    expect(parse("pageSize=9999").pageSize).toBe(200);
    expect(parse("pageSize=abc").pageSize).toBe(
      DEFAULT_RISK_CONTROL_REGISTRY_STATE.pageSize,
    );
  });

  it("reads boolean toggles", () => {
    expect(parse("overdueOnly=true").overdueOnly).toBe(true);
    expect(parse("awaitingVerification=true").awaitingVerification).toBe(true);
    expect(parse("includeTerminal=true").includeTerminal).toBe(true);
    expect(parse("overdueOnly=maybe").overdueOnly).toBe(false);
  });
});

describe("serializeRiskControlRegistrySearchParams", () => {
  it("omits defaults so clean URLs stay clean", () => {
    const params = serializeRiskControlRegistrySearchParams(
      DEFAULT_RISK_CONTROL_REGISTRY_STATE,
    );
    expect(params.toString()).toBe("");
  });

  it("round-trips a fully populated state", () => {
    const state = {
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      search: "guard",
      status: "implemented" as const,
      hierarchyLevel: "engineering" as const,
      controlNature: "preventive" as const,
      effectiveness: "partially_effective" as const,
      hazardId: "hz-1",
      riskAssessmentId: "ra-1",
      ownerReference: "EMP-7",
      overdueOnly: true,
      awaitingVerification: true,
      includeTerminal: true,
      reviewDueBefore: "2027-01-01",
      reviewDueAfter: "2026-01-01",
      page: 3,
      pageSize: 50,
    };
    expect(
      parseRiskControlRegistrySearchParams(
        serializeRiskControlRegistrySearchParams(state),
      ),
    ).toEqual(state);
  });
});

describe("registryStateToListParams", () => {
  it("converts page/pageSize into offset/limit", () => {
    const params = registryStateToListParams({
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      page: 3,
      pageSize: 25,
    });
    expect(params.offset).toBe(50);
    expect(params.limit).toBe(25);
  });

  it("sends date filters as ISO datetimes", () => {
    const params = registryStateToListParams({
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      reviewDueBefore: "2027-01-01",
    });
    expect(params.review_due_before).toBe("2027-01-01T00:00:00Z");
  });

  it("omits falsy filters entirely", () => {
    const params = registryStateToListParams(
      DEFAULT_RISK_CONTROL_REGISTRY_STATE,
    );
    expect(params).toEqual({ offset: 0, limit: 25 });
  });

  it("drops malformed date filter values instead of forwarding them to the API", () => {
    const bogusBefore = registryStateToListParams({
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      reviewDueBefore: "bogus",
    });
    expect(bogusBefore.review_due_before).toBeUndefined();

    const shapeInvalidAfter = registryStateToListParams({
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      reviewDueAfter: "2027-13-99",
    });
    // Matches the risk-assessments precedent: shape-only regex guard, not full
    // calendar validation. "2027-13-99" matches YYYY-MM-DD shape, so it is
    // still forwarded (the backend is responsible for semantic date validation).
    expect(shapeInvalidAfter.review_due_after).toBe("2027-13-99T00:00:00Z");

    const bogusAfter = registryStateToListParams({
      ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
      reviewDueAfter: "not-a-date",
    });
    expect(bogusAfter.review_due_after).toBeUndefined();
  });
});

describe("hasActiveRiskControlRegistryFilters", () => {
  it("is false for defaults and true for any change", () => {
    expect(
      hasActiveRiskControlRegistryFilters(DEFAULT_RISK_CONTROL_REGISTRY_STATE),
    ).toBe(false);
    expect(
      hasActiveRiskControlRegistryFilters({
        ...DEFAULT_RISK_CONTROL_REGISTRY_STATE,
        overdueOnly: true,
      }),
    ).toBe(true);
  });
});

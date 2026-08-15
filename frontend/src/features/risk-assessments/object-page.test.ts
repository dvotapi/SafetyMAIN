import { describe, expect, it } from "vitest";

import type {
  ControlMeasure,
  RelatedRiskControlSummary,
} from "@/features/risk-assessments/types/risk-assessment-types";
import { relatedControlsEmptyKind } from "@/features/risk-assessments/utils/related-controls-empty";
import {
  availableLifecycleActions,
  canEditRiskAssessmentFields,
  mapRiskAssessmentCapabilities,
} from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";

const proposed: ControlMeasure = {
  id: null,
  controlType: "ppe",
  description: "Gloves",
  responsible: null,
  implemented: false,
  effective: null,
};

const materialized: RelatedRiskControlSummary = {
  id: "rc-1",
  code: "RC-1",
  title: "Gloves",
  hierarchyLevel: "ppe",
  lifecycleStatus: "active",
  ownerLabel: "Ops",
  latestEffectivenessResult: null,
  nextReviewDate: null,
};

describe("relatedControlsEmptyKind", () => {
  it("distinguishes no proposed controls", () => {
    expect(relatedControlsEmptyKind([], [])).toBe("no_proposed");
  });

  it("distinguishes proposed but not materialized", () => {
    expect(relatedControlsEmptyKind([proposed], [])).toBe("not_materialized");
  });

  it("returns null when materialized controls exist", () => {
    expect(relatedControlsEmptyKind([proposed], [materialized])).toBeNull();
    expect(relatedControlsEmptyKind([], [materialized])).toBeNull();
  });
});

describe("object page lifecycle gates (Phase 3)", () => {
  const caps = mapRiskAssessmentCapabilities(() => true);

  it("allows draft edit only for draft + update permission", () => {
    expect(canEditRiskAssessmentFields({ status: "draft" }, caps)).toBe(true);
    expect(canEditRiskAssessmentFields({ status: "under_review" }, caps)).toBe(
      false,
    );
  });

  it("offers submit only for draft with inherent risk and approve only for under_review", () => {
    expect(
      availableLifecycleActions({ status: "draft", inherentRisk: null }, caps),
    ).toEqual(["archive"]);
    expect(
      availableLifecycleActions(
        {
          status: "draft",
          inherentRisk: { level: "low", factors: [], explanation: "" },
        },
        caps,
      ),
    ).toEqual(["submit_for_review", "archive"]);
    expect(
      availableLifecycleActions(
        { status: "under_review", inherentRisk: null },
        caps,
      ),
    ).toEqual(["approve", "archive"]);
  });

  it("hides lifecycle actions without permissions", () => {
    const none = mapRiskAssessmentCapabilities(() => false);
    expect(
      availableLifecycleActions(
        {
          status: "draft",
          inherentRisk: { level: "low", factors: [], explanation: "" },
        },
        none,
      ),
    ).toEqual([]);
    expect(
      availableLifecycleActions(
        { status: "under_review", inherentRisk: null },
        none,
      ),
    ).toEqual([]);
  });
});

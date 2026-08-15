import { describe, expect, it } from "vitest";

import { defaultRiskAssessmentFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import {
  resetEvaluationForProfile,
  shouldPatchRiskInputsAfterCreate,
} from "@/features/risk-assessments/utils/create-workflow";

describe("create workflow helpers", () => {
  it("does not patch when only create fields are filled", () => {
    expect(
      shouldPatchRiskInputsAfterCreate({
        ...defaultRiskAssessmentFormValues,
        hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
        code: "RA-1",
        title: "Test",
        assessedObjectReference: "Bay 1",
      }),
    ).toBe(false);
  });

  it("patches when inherent risk, controls, or acceptance are present", () => {
    expect(
      shouldPatchRiskInputsAfterCreate({
        ...defaultRiskAssessmentFormValues,
        inherentRisk: {
          ...defaultRiskAssessmentFormValues.inherentRisk,
          probabilityScore: 2,
          severityScore: 3,
        },
      }),
    ).toBe(true);

    expect(
      shouldPatchRiskInputsAfterCreate({
        ...defaultRiskAssessmentFormValues,
        controls: [
          {
            id: null,
            controlType: "ppe",
            description: "Gloves",
            responsible: "",
            implemented: false,
            effective: null,
          },
        ],
      }),
    ).toBe(true);

    expect(
      shouldPatchRiskInputsAfterCreate({
        ...defaultRiskAssessmentFormValues,
        acceptanceDecision: "accepted",
      }),
    ).toBe(true);
  });

  it("resets evaluation extras for a profile", () => {
    const reset = resetEvaluationForProfile([
      "probability",
      "severity",
      "business_impact",
    ]);
    expect(reset.probabilityScore).toBeNull();
    expect(reset.extraFactorScores).toEqual({ business_impact: null });
  });
});

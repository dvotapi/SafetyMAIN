import { describe, expect, it, vi } from "vitest";

import { defaultRiskAssessmentFormValues } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessment } from "@/features/risk-assessments/types/risk-assessment-types";
import {
  orchestrateRiskAssessmentCreate,
  orchestrateRiskAssessmentPatchRetry,
} from "@/features/risk-assessments/utils/create-orchestration";
import { mapRiskAssessmentValidationDetails } from "@/features/risk-assessments/utils/map-validation-errors";
import { createSubmitLock } from "@/features/risk-assessments/utils/submit-lock";

const baseValues = {
  ...defaultRiskAssessmentFormValues,
  hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
  code: "RA-1",
  title: "Create orchestration",
  assessedObjectReference: "Bay 1",
};

function sampleAssessment(
  overrides: Partial<RiskAssessment> = {},
): RiskAssessment {
  return {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    organizationId: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    hazardId: baseValues.hazardId,
    code: "RA-1",
    title: "Create orchestration",
    assessmentProfile: "simple_3x3",
    assessedObject: {
      objectType: "workplace",
      reference: "Bay 1",
    },
    assessorId: "user-1",
    assessmentDate: "2026-08-01",
    reviewSchedule: {
      reviewDueDate: null,
      reviewFrequencyDays: null,
      reviewReason: null,
      triggeredBy: null,
    },
    inherentRisk: null,
    residualRisk: null,
    controls: [],
    acceptance: null,
    competencyRequirements: [],
    extensionReferences: {},
    status: "draft",
    supersededById: null,
    archivedAt: null,
    archivedBy: null,
    approvedAt: null,
    approvedBy: null,
    createdAt: "2026-08-01T00:00:00Z",
    updatedAt: "2026-08-01T00:00:00Z",
    version: 1,
    ...overrides,
  };
}

describe("orchestrateRiskAssessmentCreate", () => {
  it("POST success with no PATCH required", async () => {
    const create = vi.fn(async () => sampleAssessment());
    const update = vi.fn(async () => sampleAssessment({ version: 2 }));

    const result = await orchestrateRiskAssessmentCreate(baseValues, {
      create,
      update,
    });

    expect(result.status).toBe("created");
    if (result.status === "created") {
      expect(result.patched).toBe(false);
      expect(result.assessment.id).toBe("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    }
    expect(create).toHaveBeenCalledTimes(1);
    expect(update).not.toHaveBeenCalled();
  });

  it("POST success followed by PATCH success", async () => {
    const created = sampleAssessment();
    const updated = sampleAssessment({
      version: 2,
      inherentRisk: {
        level: "medium",
        factors: [
          { factor: "probability", score: 2 },
          { factor: "severity", score: 3 },
        ],
        explanation: "ok",
      },
    });
    const create = vi.fn(async () => created);
    const update = vi.fn(async () => updated);

    const result = await orchestrateRiskAssessmentCreate(
      {
        ...baseValues,
        inherentRisk: {
          ...baseValues.inherentRisk,
          probabilityScore: 2,
          severityScore: 3,
        },
      },
      { create, update },
    );

    expect(result.status).toBe("created");
    if (result.status === "created") {
      expect(result.patched).toBe(true);
      expect(result.assessment.version).toBe(2);
    }
    expect(create).toHaveBeenCalledTimes(1);
    expect(update).toHaveBeenCalledTimes(1);
    expect(update).toHaveBeenCalledWith(
      created.id,
      expect.objectContaining({ expected_version: 1 }),
    );
  });

  it("POST success followed by PATCH failure preserves draft", async () => {
    const created = sampleAssessment();
    const patchError = new Error("patch failed");
    const create = vi.fn(async () => created);
    const update = vi.fn(async () => {
      throw patchError;
    });

    const result = await orchestrateRiskAssessmentCreate(
      {
        ...baseValues,
        acceptanceDecision: "accepted",
        acceptanceJustification: "Within tolerance",
      },
      { create, update },
    );

    expect(result.status).toBe("partial_failure");
    if (result.status === "partial_failure") {
      expect(result.assessment.id).toBe(created.id);
      expect(result.assessment.version).toBe(1);
      expect(result.patchError).toBe(patchError);
    }
    expect(create).toHaveBeenCalledTimes(1);
    expect(update).toHaveBeenCalledTimes(1);
  });
});

describe("orchestrateRiskAssessmentPatchRetry", () => {
  it("PATCH-only retry after partial failure", async () => {
    const update = vi.fn(async () => sampleAssessment({ version: 2 }));
    const create = vi.fn();

    const result = await orchestrateRiskAssessmentPatchRetry(
      {
        ...baseValues,
        inherentRisk: {
          ...baseValues.inherentRisk,
          probabilityScore: 1,
          severityScore: 2,
        },
      },
      "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      1,
      { update },
    );

    expect(result.status).toBe("updated");
    if (result.status === "updated") {
      expect(result.assessment.version).toBe(2);
    }
    expect(update).toHaveBeenCalledTimes(1);
    expect(create).not.toHaveBeenCalled();
  });

  it("retry never performs a second POST", async () => {
    const create = vi.fn();
    const update = vi.fn(async () => sampleAssessment({ version: 2 }));

    // Simulate page wiring: retry path only receives update.
    await orchestrateRiskAssessmentPatchRetry(
      {
        ...baseValues,
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
      },
      "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      1,
      { update },
    );

    expect(update).toHaveBeenCalledTimes(1);
    expect(create).not.toHaveBeenCalled();
  });
});

describe("createSubmitLock", () => {
  it("blocks duplicate submit before navigation completes", () => {
    const lock = createSubmitLock();
    expect(lock.tryAcquire()).toBe(true);
    // Success path keeps the lock — second click must not start another create.
    expect(lock.tryAcquire()).toBe(false);
    expect(lock.isLocked()).toBe(true);

    lock.release();
    expect(lock.tryAcquire()).toBe(true);
  });
});

describe("mapRiskAssessmentValidationDetails", () => {
  it("maps known field paths including nested risk and controls", () => {
    const mapped = mapRiskAssessmentValidationDetails(
      {
        title: ["Title is required"],
        assessed_object: {
          reference: ["Reference is required"],
        },
        inherent_risk: {
          probability: ["Must be between 1 and 5"],
        },
        residual_risk: {
          severity: ["Must be between 1 and 5"],
        },
        controls: {
          "0": {
            description: ["Description is required"],
          },
        },
        acceptance: {
          decision: ["Invalid decision"],
        },
        review_schedule: {
          review_due_date: ["Invalid date"],
        },
      },
      "Validation failed",
    );

    expect(mapped.fieldErrors).toEqual(
      expect.arrayContaining([
        { name: "title", message: "Title is required" },
        {
          name: "assessedObjectReference",
          message: "Reference is required",
        },
        {
          name: "inherentRisk.probabilityScore",
          message: "Must be between 1 and 5",
        },
        {
          name: "residualRisk.severityScore",
          message: "Must be between 1 and 5",
        },
        {
          name: "controls.0.description",
          message: "Description is required",
        },
        { name: "acceptanceDecision", message: "Invalid decision" },
        { name: "reviewDueDate", message: "Invalid date" },
      ]),
    );
    expect(mapped.rootMessage).toBeNull();
  });

  it("maps violation locations and uses root fallback for unknown paths", () => {
    const mapped = mapRiskAssessmentValidationDetails(
      {
        violations: [
          {
            location: ["body", "assessment_profile"],
            message: "Unknown profile",
          },
          {
            location: ["body", "extension_references", "legacy"],
            message: "Unsupported extension",
          },
          {
            location: ["body", "inherent_risk", "factors", "0", "score"],
            message: "Factor score invalid",
          },
        ],
      },
      "Validation failed",
    );

    expect(mapped.fieldErrors).toEqual(
      expect.arrayContaining([
        { name: "assessmentProfile", message: "Unknown profile" },
        {
          name: "inherentRisk",
          message: "Factor score invalid",
        },
      ]),
    );
    expect(mapped.rootMessage).toContain("extension_references.legacy");
    expect(mapped.rootMessage).toContain("Unsupported extension");
  });

  it("falls back to root message when details are empty", () => {
    const mapped = mapRiskAssessmentValidationDetails(
      null,
      "Validation failed",
    );
    expect(mapped.fieldErrors).toEqual([]);
    expect(mapped.rootMessage).toBe("Validation failed");
  });
});

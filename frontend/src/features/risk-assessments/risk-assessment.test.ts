import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import { mapRiskControlOwnerLabel } from "@/features/risk-assessments/api/risk-assessment-api";
import {
  hazardRelatedRiskAssessmentsPredicate,
  invalidateHazardRelatedRiskAssessments,
  isHazardRelatedRiskAssessmentsQueryKey,
} from "@/features/risk-assessments/api/invalidate-hazard-related";
import { riskAssessmentKeys } from "@/features/risk-assessments/api/risk-assessment-query-keys";
import {
  availableLifecycleActions,
  canEditRiskAssessmentFields,
  mapRiskAssessmentCapabilities,
} from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import {
  evaluationToFormValues,
  formValuesToCreateRequest,
  formValuesToEvaluationRequest,
  formValuesToUpdateRequest,
  mapRiskAssessmentDto,
  riskAssessmentToFormValues,
} from "@/features/risk-assessments/mappers/risk-assessment-mappers";
import {
  defaultRiskAssessmentFormValues,
  emptyRiskEvaluationFormValues,
  riskAssessmentFormSchema,
} from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type { RiskAssessmentDto } from "@/features/risk-assessments/types/risk-assessment-types";
import {
  ASSESSMENT_PROFILE_CATALOG,
  extraFactorIds,
  getAssessmentProfileCatalogEntry,
} from "@/features/risk-assessments/utils/assessment-profiles";
import {
  hasActiveRiskAssessmentRegistryFilters,
  parseRiskAssessmentRegistrySearchParams,
  registryStateToListParams,
  serializeRiskAssessmentRegistrySearchParams,
} from "@/features/risk-assessments/utils/risk-assessment-filters";
import {
  hierarchyRank,
  isHigherOnHierarchy,
  sortControlsByHierarchy,
} from "@/features/risk-assessments/utils/hierarchy-of-controls";
import {
  riskAssessmentStatusLabel,
  riskAssessmentStatusToVisual,
  riskLevelLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";

const sampleDto: RiskAssessmentDto = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  organization_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  hazard_id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
  code: "RA-1",
  title: "Machine guarding assessment",
  assessment_profile: "corporate_custom",
  assessed_object: { object_type: "equipment", reference: "Press-01" },
  assessor_id: "dddddddd-dddd-dddd-dddd-dddddddddddd",
  assessment_date: "2026-08-01T00:00:00Z",
  review_schedule: {
    review_due_date: "2027-08-01T00:00:00Z",
    review_frequency_days: 365,
    review_reason: "periodic",
    triggered_by: "periodic_review",
  },
  inherent_risk: {
    factors: [
      { factor: "probability", score: 3 },
      { factor: "severity", score: 4 },
      { factor: "business_impact", score: 2 },
    ],
    level: "high",
    explanation: "Unguarded point of operation",
  },
  residual_risk: {
    factors: [
      { factor: "probability", score: 2 },
      { factor: "severity", score: 3 },
      { factor: "business_impact", score: 1 },
    ],
    level: "medium",
    explanation: "After engineering control",
  },
  controls: [
    {
      id: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
      control_type: "engineering",
      description: "Install interlocked guard",
      responsible: "Maintenance",
      implemented: false,
      effective: null,
    },
  ],
  acceptance: null,
  competency_requirements: ["loto"],
  extension_references: {},
  status: "draft",
  superseded_by_id: null,
  archived_at: null,
  archived_by: null,
  approved_at: null,
  approved_by: null,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  version: 1,
};

describe("risk assessment mappers", () => {
  it("maps dto to view model", () => {
    const assessment = mapRiskAssessmentDto(sampleDto);
    expect(assessment.code).toBe("RA-1");
    expect(assessment.organizationId).toBe(sampleDto.organization_id);
    expect(assessment.assessedObject.objectType).toBe("equipment");
    expect(assessment.inherentRisk?.level).toBe("high");
    expect(assessment.controls[0]?.controlType).toBe("engineering");
  });

  it("maps form values to create request without update-only fields", () => {
    const body = formValuesToCreateRequest({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: " RA-2 ",
      title: " Title ",
      assessmentProfile: "simple_3x3",
      assessedObjectType: "workplace",
      assessedObjectReference: " Line A ",
      inherentRisk: {
        probabilityScore: 2,
        severityScore: 3,
        extraFactorScores: {},
        explanation: "should not appear on create",
      },
    });
    expect(body.code).toBe("RA-2");
    expect(body.title).toBe("Title");
    expect(body.assessed_object).toEqual({
      object_type: "workplace",
      reference: "Line A",
    });
    expect(body).not.toHaveProperty("inherent_risk");
    expect(body).not.toHaveProperty("controls");
    expect(body).not.toHaveProperty("submit_for_review");
    expect(body).not.toHaveProperty("extension_references");
  });

  it("normalizes date-only form values to ISO datetime for the API", () => {
    const body = formValuesToCreateRequest({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-DATE",
      title: "Date check",
      assessedObjectReference: "Bay",
      assessmentDate: "2026-08-01",
      reviewDueDate: "2026-09-01",
    });
    expect(body.assessment_date).toBe("2026-08-01T00:00:00Z");
    expect(body.review_schedule?.review_due_date).toBe("2026-09-01T00:00:00Z");
  });

  it("returns null for explanation-only evaluation", () => {
    expect(
      formValuesToEvaluationRequest({
        ...emptyRiskEvaluationFormValues,
        explanation: "notes only",
      }),
    ).toBeNull();
  });

  it("returns null for probability-only evaluation", () => {
    expect(
      formValuesToEvaluationRequest({
        ...emptyRiskEvaluationFormValues,
        probabilityScore: 3,
      }),
    ).toBeNull();
  });

  it("returns null for severity-only evaluation", () => {
    expect(
      formValuesToEvaluationRequest({
        ...emptyRiskEvaluationFormValues,
        severityScore: 4,
      }),
    ).toBeNull();
  });

  it("maps a complete evaluation correctly without authoritative level", () => {
    const request = formValuesToEvaluationRequest(
      {
        probabilityScore: 3,
        severityScore: 4,
        extraFactorScores: { business_impact: 2 },
        explanation: "Unguarded point of operation",
      },
      "corporate_custom",
    );
    expect(request).toEqual({
      explanation: "Unguarded point of operation",
      probability: 3,
      severity: 4,
      factors: [
        { factor: "probability", score: 3 },
        { factor: "severity", score: 4 },
        { factor: "business_impact", score: 2 },
      ],
    });
    expect(request).not.toHaveProperty("level");
  });

  it("round-trips residual evaluation factors", () => {
    const assessment = mapRiskAssessmentDto(sampleDto);
    const formEval = evaluationToFormValues(assessment.residualRisk);
    expect(formEval.probabilityScore).toBe(2);
    expect(formEval.severityScore).toBe(3);
    expect(formEval.extraFactorScores.business_impact).toBe(1);
    expect(formEval.explanation).toBe("After engineering control");

    const request = formValuesToEvaluationRequest(formEval, "corporate_custom");
    expect(request?.probability).toBe(2);
    expect(request?.severity).toBe(3);
    expect(request?.factors).toEqual(
      expect.arrayContaining([
        { factor: "probability", score: 2 },
        { factor: "severity", score: 3 },
        { factor: "business_impact", score: 1 },
      ]),
    );
  });

  it("builds update request with risk inputs and optional submit flag", () => {
    const form = riskAssessmentToFormValues(mapRiskAssessmentDto(sampleDto));
    const body = formValuesToUpdateRequest(form, 2, {
      submitForReview: true,
      includeRiskInputs: true,
    });
    expect(body.expected_version).toBe(2);
    expect(body.submit_for_review).toBe(true);
    expect(body.inherent_risk?.factors).toEqual(
      expect.arrayContaining([{ factor: "business_impact", score: 2 }]),
    );
    expect(body.controls?.[0]?.control_type).toBe("engineering");
  });
});

describe("risk control owner mapping", () => {
  it("maps display_name_snapshot with owner_reference fallback", () => {
    expect(
      mapRiskControlOwnerLabel({
        owner_type: "user",
        owner_reference: "user-1",
        display_name_snapshot: "Ada Lovelace",
        assigned_at: "2026-08-01T00:00:00Z",
        assigned_by: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      }),
    ).toBe("Ada Lovelace");

    expect(
      mapRiskControlOwnerLabel({
        owner_type: "user",
        owner_reference: "user-1",
        display_name_snapshot: "  ",
        assigned_at: "2026-08-01T00:00:00Z",
        assigned_by: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      }),
    ).toBe("user-1");

    expect(mapRiskControlOwnerLabel(null)).toBeNull();
  });
});

describe("assessment profile catalog", () => {
  it("exposes minimal fields and extra factors", () => {
    expect(ASSESSMENT_PROFILE_CATALOG.length).toBeGreaterThanOrEqual(9);
    const corporate = getAssessmentProfileCatalogEntry("corporate_custom");
    expect(corporate?.matrixSize).toBe(5);
    expect(extraFactorIds(corporate!)).toEqual(["business_impact"]);
  });
});

describe("hierarchy of controls", () => {
  it("orders by preference", () => {
    expect(isHigherOnHierarchy("elimination", "ppe")).toBe(true);
    expect(hierarchyRank("ppe")).toBeGreaterThan(hierarchyRank("engineering"));
    const sorted = sortControlsByHierarchy([
      { controlType: "ppe" as const },
      { controlType: "elimination" as const },
    ]);
    expect(sorted.map((item) => item.controlType)).toEqual([
      "elimination",
      "ppe",
    ]);
  });
});

describe("risk assessment status", () => {
  it("maps status and risk level to labels without relying on color alone", () => {
    expect(riskAssessmentStatusToVisual("under_review")).toBe("under_review");
    expect(riskAssessmentStatusLabel("under_review")).toBe("Under Review");
    expect(riskLevelLabel("high")).toBe("High");
  });
});

describe("risk assessment permissions", () => {
  it("maps submit capability from risk:update", () => {
    const caps = mapRiskAssessmentCapabilities(
      (p) => p === "risk:read" || p === "risk:update",
    );
    expect(caps.canRead).toBe(true);
    expect(caps.canUpdateDraft).toBe(true);
    expect(caps.canSubmitForReview).toBe(true);
    expect(caps.canApprove).toBe(false);
    expect(caps.canCreate).toBe(false);
  });

  it("offers Approve only for under_review and Submit only with inherent risk", () => {
    const admin = mapRiskAssessmentCapabilities(() => true);
    expect(
      availableLifecycleActions({ status: "draft", inherentRisk: null }, admin),
    ).toEqual(["archive"]);
    expect(
      availableLifecycleActions(
        {
          status: "draft",
          inherentRisk: {
            level: "medium",
            factors: [],
            explanation: "",
          },
        },
        admin,
      ),
    ).toEqual(["submit_for_review", "archive"]);
    expect(
      availableLifecycleActions(
        { status: "under_review", inherentRisk: null },
        admin,
      ),
    ).toEqual(["approve", "archive"]);
    expect(
      availableLifecycleActions(
        { status: "approved", inherentRisk: null },
        admin,
      ),
    ).toEqual(["archive"]);
  });

  it("allows edit only for draft with update permission", () => {
    const updater = mapRiskAssessmentCapabilities((p) => p === "risk:update");
    expect(canEditRiskAssessmentFields({ status: "draft" }, updater)).toBe(
      true,
    );
    expect(
      canEditRiskAssessmentFields({ status: "under_review" }, updater),
    ).toBe(false);
    expect(
      canEditRiskAssessmentFields(
        { status: "draft" },
        mapRiskAssessmentCapabilities(() => false),
      ),
    ).toBe(false);
  });
});

describe("risk assessment query keys", () => {
  it("scopes by organization and omits profiles and forHazard keys", () => {
    expect(riskAssessmentKeys.detail("org-a", "ra1")).not.toEqual(
      riskAssessmentKeys.detail("org-b", "ra1"),
    );
    expect(riskAssessmentKeys).not.toHaveProperty("profiles");
    expect(riskAssessmentKeys).not.toHaveProperty("forHazard");
  });
});

describe("boundary-safe hazard related invalidation", () => {
  it("recognizes the Hazard related-RA key shape", () => {
    expect(
      isHazardRelatedRiskAssessmentsQueryKey(
        ["hazards", "org-1", "detail", "h1", "risk-assessments"],
        { organizationId: "org-1", hazardId: "h1" },
      ),
    ).toBe(true);
    expect(
      isHazardRelatedRiskAssessmentsQueryKey(
        ["hazards", "org-2", "detail", "h1", "risk-assessments"],
        { organizationId: "org-1" },
      ),
    ).toBe(false);
    expect(
      isHazardRelatedRiskAssessmentsQueryKey([
        "risk-assessments",
        "org-1",
        "list",
      ]),
    ).toBe(false);
  });

  it("null organizationId matches only the none bucket, not other orgs", async () => {
    const client = new QueryClient();
    const noneKey = [
      "hazards",
      "none",
      "detail",
      "h1",
      "risk-assessments",
    ] as const;
    const orgKey = [
      "hazards",
      "org-1",
      "detail",
      "h1",
      "risk-assessments",
    ] as const;
    client.setQueryData(noneKey, []);
    client.setQueryData(orgKey, []);

    expect(
      isHazardRelatedRiskAssessmentsQueryKey(noneKey, {
        organizationId: null,
      }),
    ).toBe(true);
    expect(
      isHazardRelatedRiskAssessmentsQueryKey(orgKey, {
        organizationId: null,
      }),
    ).toBe(false);

    await invalidateHazardRelatedRiskAssessments(client, {
      organizationId: null,
    });

    expect(client.getQueryState(noneKey)?.isInvalidated).toBe(true);
    expect(client.getQueryState(orgKey)?.isInvalidated).toBe(false);
  });

  it("invalidates matching Hazard related queries by predicate", async () => {
    const client = new QueryClient();
    const matchingKey = [
      "hazards",
      "org-1",
      "detail",
      "h1",
      "risk-assessments",
    ] as const;
    const otherOrgKey = [
      "hazards",
      "org-2",
      "detail",
      "h1",
      "risk-assessments",
    ] as const;
    const otherFeatureKey = riskAssessmentKeys.list("org-1", { limit: 10 });

    client.setQueryData(matchingKey, [{ id: "ra-1" }]);
    client.setQueryData(otherOrgKey, [{ id: "ra-2" }]);
    client.setQueryData(otherFeatureKey, { items: [], pagination: {} });

    await invalidateHazardRelatedRiskAssessments(client, {
      organizationId: "org-1",
      hazardId: "h1",
    });

    expect(client.getQueryState(matchingKey)?.isInvalidated).toBe(true);
    expect(client.getQueryState(otherOrgKey)?.isInvalidated).toBe(false);
    expect(client.getQueryState(otherFeatureKey)?.isInvalidated).toBe(false);
  });

  it("predicate can invalidate all hazards related-RA keys for an org", async () => {
    const client = new QueryClient();
    const h1 = [
      "hazards",
      "org-1",
      "detail",
      "h1",
      "risk-assessments",
    ] as const;
    const h2 = [
      "hazards",
      "org-1",
      "detail",
      "h2",
      "risk-assessments",
    ] as const;
    client.setQueryData(h1, []);
    client.setQueryData(h2, []);

    await client.invalidateQueries({
      predicate: hazardRelatedRiskAssessmentsPredicate({
        organizationId: "org-1",
      }),
    });

    expect(client.getQueryState(h1)?.isInvalidated).toBe(true);
    expect(client.getQueryState(h2)?.isInvalidated).toBe(true);
  });
});

describe("registry url state", () => {
  it("parses and serializes supported filters only", () => {
    const state = parseRiskAssessmentRegistrySearchParams(
      new URLSearchParams(
        "search=guard&status=under_review&hazardId=h1&page=2&includeArchived=true",
      ),
    );
    expect(state.search).toBe("guard");
    expect(state.status).toBe("under_review");
    expect(state.hazardId).toBe("h1");
    expect(state.page).toBe(2);
    expect(hasActiveRiskAssessmentRegistryFilters(state)).toBe(true);
    const params = serializeRiskAssessmentRegistrySearchParams(state);
    expect(params.get("search")).toBe("guard");
    expect(registryStateToListParams(state).offset).toBe(25);
    expect(registryStateToListParams(state).hazard_id).toBe("h1");
  });

  it("ignores invalid enums and unsupported filter keys", () => {
    const state = parseRiskAssessmentRegistrySearchParams(
      new URLSearchParams("status=nope&riskBand=high&sort=title"),
    );
    expect(state.status).toBe("");
    expect(registryStateToListParams(state)).not.toHaveProperty("sort");
  });
});

describe("risk assessment form schema", () => {
  it("requires assessed object reference", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "",
    });
    expect(result.success).toBe(false);
  });

  it("allows entirely empty evaluation sections", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "Bay 1",
      assessmentProfile: "corporate_custom",
    });
    expect(result.success).toBe(true);
  });

  it("rejects score 4 or 5 for simple_3x3", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "Bay 1",
      assessmentProfile: "simple_3x3",
      inherentRisk: {
        probabilityScore: 4,
        severityScore: 2,
        extraFactorScores: {},
        explanation: "",
      },
    });
    expect(result.success).toBe(false);
    expect(
      result.success
        ? []
        : result.error.issues.some(
            (issue) => issue.path.join(".") === "inherentRisk.probabilityScore",
          ),
    ).toBe(true);
  });

  it("accepts score 5 for 5x5 profiles", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "Bay 1",
      assessmentProfile: "simple_5x5",
      inherentRisk: {
        probabilityScore: 5,
        severityScore: 5,
        extraFactorScores: {},
        explanation: "",
      },
    });
    expect(result.success).toBe(true);
  });

  it("requires missing extra factor for corporate_custom when evaluation is present", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "Bay 1",
      assessmentProfile: "corporate_custom",
      inherentRisk: {
        probabilityScore: 2,
        severityScore: 3,
        extraFactorScores: {},
        explanation: "",
      },
    });
    expect(result.success).toBe(false);
    expect(
      result.success
        ? []
        : result.error.issues.some(
            (issue) =>
              issue.path.join(".") ===
              "inherentRisk.extraFactorScores.business_impact",
          ),
    ).toBe(true);
  });

  it("accepts required extra factor when present", () => {
    const result = riskAssessmentFormSchema.safeParse({
      ...defaultRiskAssessmentFormValues,
      hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      code: "RA-9",
      title: "Test",
      assessedObjectReference: "Bay 1",
      assessmentProfile: "corporate_custom",
      inherentRisk: {
        probabilityScore: 2,
        severityScore: 3,
        extraFactorScores: { business_impact: 2 },
        explanation: "",
      },
    });
    expect(result.success).toBe(true);
  });
});

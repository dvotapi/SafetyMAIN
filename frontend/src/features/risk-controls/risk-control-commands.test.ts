import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import {
  assessmentRelatedControlsPredicate,
  invalidateAssessmentRelatedControls,
  isAssessmentRelatedControlsQueryKey,
} from "@/features/risk-controls/api/invalidate-assessment-related";
import { materializeRiskControls } from "@/features/risk-controls/api/risk-control-commands";
import { riskControlKeys } from "@/features/risk-controls/api/risk-control-query-keys";
import { apiClient } from "@/services/api/client";
import type {
  AssignOwnerDto,
  CompleteImplementationDto,
  CompleteReviewDto,
  EvidenceRequestDto,
  MaterializeControlsDto,
  PlanRiskControlDto,
  ProgressDto,
  ReasonVersionDto,
  ScheduleReviewDto,
  SupersedeDto,
  SuspendDto,
  VerificationRequestDto,
  VersionOnlyDto,
} from "@/features/risk-controls/types/risk-control-dto";

describe("risk control command request DTOs", () => {
  it("every command DTO requires expected_version", () => {
    const assignOwner: AssignOwnerDto = {
      expected_version: 1,
      owner: {
        owner_type: "user",
        owner_reference: "user-1",
        display_name_snapshot: "Jane Doe",
      },
    };
    const plan: PlanRiskControlDto = {
      expected_version: 1,
      implementation: {},
    };
    const versionOnly: VersionOnlyDto = { expected_version: 1 };
    const progress: ProgressDto = { expected_version: 1, progress: 50 };
    const evidence: EvidenceRequestDto = {
      expected_version: 1,
      evidence_type: "document",
      external_reference: "ref-1",
      title: "Evidence title",
    };
    const completeImplementation: CompleteImplementationDto = {
      expected_version: 1,
      summary: "Done",
    };
    const verification: VerificationRequestDto = {
      expected_version: 1,
      method: "inspection",
      result: "effective",
    };
    const scheduleReview: ScheduleReviewDto = {
      expected_version: 1,
      schedule: {},
    };
    const completeReview: CompleteReviewDto = {
      expected_version: 1,
      verification,
    };
    const suspend: SuspendDto = { expected_version: 1, reason: "paused" };
    const supersede: SupersedeDto = {
      expected_version: 1,
      replacement_control_id: "rc-2",
      reason: "replaced",
    };
    const reasonVersion: ReasonVersionDto = {
      expected_version: 1,
      reason: "archived",
    };

    for (const dto of [
      assignOwner,
      plan,
      versionOnly,
      progress,
      evidence,
      completeImplementation,
      verification,
      scheduleReview,
      completeReview,
      suspend,
      supersede,
      reasonVersion,
    ]) {
      expect(dto.expected_version).toBe(1);
    }
  });

  it("materialize DTO has no optimistic-concurrency field", () => {
    const materialize: MaterializeControlsDto = { allow_under_review: true };
    expect(materialize).not.toHaveProperty("expected_version");
  });
});

describe("materializeRiskControls", () => {
  it("posts to the risk-assessments materialize-controls path", async () => {
    const requestSpy = vi
      .spyOn(apiClient, "request")
      .mockResolvedValue({ items: [] });

    await materializeRiskControls("ra-1", { allow_under_review: false });

    expect(requestSpy).toHaveBeenCalledWith({
      method: "POST",
      path: "/api/v1/risk-assessments/ra-1/materialize-controls",
      body: { allow_under_review: false },
    });

    requestSpy.mockRestore();
  });
});

describe("boundary-safe assessment related invalidation", () => {
  it("recognizes the Risk Assessment related-controls key shape", () => {
    expect(
      isAssessmentRelatedControlsQueryKey(
        ["risk-assessments", "org-1", "detail", "ra-1", "related-controls"],
        { organizationId: "org-1", riskAssessmentId: "ra-1" },
      ),
    ).toBe(true);
    expect(
      isAssessmentRelatedControlsQueryKey(
        ["risk-assessments", "org-2", "detail", "ra-1", "related-controls"],
        { organizationId: "org-1" },
      ),
    ).toBe(false);
    expect(
      isAssessmentRelatedControlsQueryKey(["risk-controls", "org-1", "list"]),
    ).toBe(false);
  });

  it("rejects a matching key from a different organization", () => {
    const key = [
      "risk-assessments",
      "org-1",
      "detail",
      "ra-1",
      "related-controls",
    ] as const;

    expect(
      isAssessmentRelatedControlsQueryKey(key, { organizationId: "org-1" }),
    ).toBe(true);
    expect(
      isAssessmentRelatedControlsQueryKey(key, { organizationId: "org-2" }),
    ).toBe(false);
  });

  it("rejects a wrong suffix", () => {
    expect(
      isAssessmentRelatedControlsQueryKey(
        ["risk-assessments", "org-1", "detail", "ra-1", "activity"],
        { organizationId: "org-1" },
      ),
    ).toBe(false);
  });

  it("filters by risk assessment id when provided", () => {
    const key = [
      "risk-assessments",
      "org-1",
      "detail",
      "ra-1",
      "related-controls",
    ] as const;

    expect(
      isAssessmentRelatedControlsQueryKey(key, {
        organizationId: "org-1",
        riskAssessmentId: "ra-1",
      }),
    ).toBe(true);
    expect(
      isAssessmentRelatedControlsQueryKey(key, {
        organizationId: "org-1",
        riskAssessmentId: "ra-2",
      }),
    ).toBe(false);
  });

  it("invalidates matching Risk Assessment related queries by predicate", async () => {
    const client = new QueryClient();
    const matchingKey = [
      "risk-assessments",
      "org-1",
      "detail",
      "ra-1",
      "related-controls",
    ] as const;
    const otherOrgKey = [
      "risk-assessments",
      "org-2",
      "detail",
      "ra-1",
      "related-controls",
    ] as const;
    const otherFeatureKey = riskControlKeys.list("org-1", { limit: 10 });

    client.setQueryData(matchingKey, [{ id: "rc-1" }]);
    client.setQueryData(otherOrgKey, [{ id: "rc-2" }]);
    client.setQueryData(otherFeatureKey, { items: [], pagination: {} });

    await invalidateAssessmentRelatedControls(client, {
      organizationId: "org-1",
      riskAssessmentId: "ra-1",
    });

    expect(client.getQueryState(matchingKey)?.isInvalidated).toBe(true);
    expect(client.getQueryState(otherOrgKey)?.isInvalidated).toBe(false);
    expect(client.getQueryState(otherFeatureKey)?.isInvalidated).toBe(false);
  });

  it("predicate can invalidate all related-control keys for an org", async () => {
    const client = new QueryClient();
    const ra1 = [
      "risk-assessments",
      "org-1",
      "detail",
      "ra-1",
      "related-controls",
    ] as const;
    const ra2 = [
      "risk-assessments",
      "org-1",
      "detail",
      "ra-2",
      "related-controls",
    ] as const;
    client.setQueryData(ra1, []);
    client.setQueryData(ra2, []);

    await client.invalidateQueries({
      predicate: assessmentRelatedControlsPredicate({
        organizationId: "org-1",
      }),
    });

    expect(client.getQueryState(ra1)?.isInvalidated).toBe(true);
    expect(client.getQueryState(ra2)?.isInvalidated).toBe(true);
  });
});

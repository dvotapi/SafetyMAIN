import { describe, expect, it } from "vitest";

import {
  availableLifecycleActions,
  mapRiskControlCapabilities,
} from "@/features/risk-controls/hooks/use-risk-control-permissions";
import type {
  RiskControl,
  RiskControlOwner,
} from "@/features/risk-controls/types/risk-control-types";
import { RISK_CONTROL_STATUSES } from "@/features/risk-controls/utils/risk-control-status";

const MEMBER_PERMISSIONS = [
  "risk_control:read",
  "risk_control:create",
  "risk_control:update",
  "risk_control:assign",
  "risk_control:implement",
  "risk_control:review",
  "risk_control:materialize",
];

function withPermissions(granted: string[]) {
  return (permission: string) => granted.includes(permission);
}

describe("mapRiskControlCapabilities", () => {
  it("grants everything to a full permission set", () => {
    const caps = mapRiskControlCapabilities(() => true);
    expect(Object.values(caps).every(Boolean)).toBe(true);
  });

  it("denies verify, suspend, supersede, archive and cancel to a member", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(MEMBER_PERMISSIONS),
    );
    expect(caps.canRead).toBe(true);
    expect(caps.canImplement).toBe(true);
    expect(caps.canReview).toBe(true);
    expect(caps.canMaterialize).toBe(true);
    expect(caps.canVerify).toBe(false);
    expect(caps.canSuspend).toBe(false);
    expect(caps.canSupersede).toBe(false);
    expect(caps.canArchive).toBe(false);
    expect(caps.canCancel).toBe(false);
  });

  it("gives an auditor read plus activity only", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(["risk_control:read", "audit:read"]),
    );
    expect(caps.canRead).toBe(true);
    expect(caps.canViewActivity).toBe(true);
    expect(caps.canUpdate).toBe(false);
    expect(caps.canAssignOwner).toBe(false);
  });

  it("requires exact permission strings — no wildcard expansion", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(["risk_control:*"]),
    );
    expect(caps.canRead).toBe(false);
  });

  it("gates related-object reads on their own feature permissions", () => {
    const caps = mapRiskControlCapabilities(
      withPermissions(["risk_control:read", "hazard:read"]),
    );
    expect(caps.canViewHazard).toBe(true);
    expect(caps.canViewAssessment).toBe(false);
  });
});

const all = mapRiskControlCapabilities(() => true);

const someOwner: RiskControlOwner = {
  ownerType: "user",
  ownerReference: "user-1",
  displayNameSnapshot: "Jane Doe",
  assignedAt: "2026-01-01T00:00:00Z",
  assignedBy: "user-2",
  label: "Jane Doe",
};

function control(overrides: Partial<RiskControl> = {}): RiskControl {
  return {
    id: "control-1",
    organizationId: "org-1",
    code: "RC-0001",
    title: "Install machine guarding",
    description: "",
    hierarchyLevel: "engineering",
    controlNature: "preventive",
    source: {
      sourceType: "manual",
      sourceReference: null,
      riskAssessmentId: null,
      sourceControlReference: null,
      assessmentVersion: null,
      assessmentApprovedAt: null,
      residualLevel: null,
      snapshot: null,
    },
    hazardId: null,
    riskAssessmentId: null,
    scope: [],
    owner: null,
    implementation: {
      targetStartDate: null,
      targetCompletionDate: null,
      actualStartDate: null,
      actualCompletionDate: null,
      implementationMethod: "",
      milestones: [],
      dependencies: [],
      resourceNotes: "",
      evidenceRequirements: [],
      progress: 0,
      summary: "",
      evidenceWaiverReason: null,
    },
    evidence: [],
    verifications: [],
    reviewSchedule: {
      reviewRequired: false,
      reviewFrequencyDays: null,
      nextReviewDate: null,
      lastReviewDate: null,
      reviewBasis: "manual",
      escalationPolicyRef: null,
      noReviewReason: null,
    },
    competencyRequirements: [],
    relatedEntities: [],
    extensionData: {},
    status: "draft",
    latestEffectivenessResult: null,
    nextReviewDate: null,
    isOverdue: false,
    verificationMethodRequirement: "",
    version: 1,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("availableLifecycleActions", () => {
  it("offers plan first for an owned draft", () => {
    const actions = availableLifecycleActions(
      control({ status: "draft", owner: someOwner }),
      all,
    );
    expect(actions[0]).toBe("plan");
  });

  it("does not offer plan for an unowned draft", () => {
    expect(
      availableLifecycleActions(control({ status: "draft", owner: null }), all),
    ).not.toContain("plan");
  });

  it("does not offer plan again once planned", () => {
    expect(
      availableLifecycleActions(
        control({ status: "planned", owner: someOwner }),
        all,
      ),
    ).not.toContain("plan");
  });

  it("offers verification as the primary action once implemented", () => {
    expect(
      availableLifecycleActions(control({ status: "implemented" }), all)[0],
    ).toBe("verify");
  });

  it("offers resume only from suspended", () => {
    expect(
      availableLifecycleActions(control({ status: "suspended" }), all),
    ).toContain("resume");
    expect(
      availableLifecycleActions(control({ status: "planned" }), all),
    ).not.toContain("resume");
  });

  it("does not offer suspend from draft", () => {
    // draft -> suspended is not a legal transition
    expect(
      availableLifecycleActions(control({ status: "draft" }), all),
    ).not.toContain("suspend");
  });

  it("offers nothing but archive from cancelled", () => {
    expect(
      availableLifecycleActions(control({ status: "cancelled" }), all),
    ).toEqual(["archive"]);
  });

  it("offers nothing from archived", () => {
    expect(
      availableLifecycleActions(control({ status: "archived" }), all),
    ).toEqual([]);
  });

  it("filters by capability, not just by state", () => {
    const noVerify = mapRiskControlCapabilities(
      (p) => p !== "risk_control:verify",
    );
    expect(
      availableLifecycleActions(control({ status: "implemented" }), noVerify),
    ).not.toContain("verify");
  });

  it("never offers a delete action", () => {
    for (const status of RISK_CONTROL_STATUSES) {
      const actions = availableLifecycleActions(control({ status }), all);
      expect(actions.some((a) => String(a).includes("delete"))).toBe(false);
    }
  });
});

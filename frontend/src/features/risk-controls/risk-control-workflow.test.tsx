import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { ImplementationPlanSection } from "@/features/risk-controls/components/implementation-plan-section";
import { ImplementationProgressSection } from "@/features/risk-controls/components/implementation-progress-section";
import {
  buildCompleteImplementationFormSchema,
  completeImplementationFormValuesToRequest,
  progressFormSchema,
  progressFormValuesToRequest,
} from "@/features/risk-controls/schemas/implementation-progress-schema";
import {
  buildImplementationFormSchema,
  planFormValuesToRequest,
} from "@/features/risk-controls/schemas/implementation-schema";
import { ownerFormValuesToRequest } from "@/features/risk-controls/schemas/owner-schema";
import type {
  RiskControl,
  RiskControlCapabilities,
  RiskControlMilestone,
} from "@/features/risk-controls/types/risk-control-types";

afterEach(() => {
  cleanup();
});

const BASE_CAPABILITIES: RiskControlCapabilities = {
  canRead: true,
  canCreate: false,
  canUpdate: false,
  canAssignOwner: true,
  canImplement: false,
  canVerify: false,
  canReview: false,
  canSuspend: false,
  canSupersede: false,
  canArchive: false,
  canCancel: false,
  canMaterialize: false,
  canViewHazard: false,
  canViewAssessment: false,
  canViewActivity: false,
};

function renderSection(
  overrides: Partial<{
    capabilities: RiskControlCapabilities;
    status: string;
    open: boolean;
    onAssign: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onOpenChange = vi.fn();
  const onAssign = overrides.onAssign ?? vi.fn();
  render(
    <ControlOwnerSection
      owner={null}
      status={overrides.status ?? "draft"}
      version={3}
      capabilities={overrides.capabilities ?? BASE_CAPABILITIES}
      open={overrides.open ?? false}
      onOpenChange={onOpenChange}
      onAssign={onAssign}
    />,
  );
  return { onOpenChange, onAssign };
}

describe("ControlOwnerSection", () => {
  it("does not render the assign button without risk_control:assign", () => {
    renderSection({
      capabilities: { ...BASE_CAPABILITIES, canAssignOwner: false },
    });

    expect(
      screen.queryByRole("button", { name: /assign owner/i }),
    ).not.toBeInTheDocument();
  });

  it("does not render the assign button when status is archived", () => {
    renderSection({ status: "archived" });

    expect(
      screen.queryByRole("button", { name: /assign owner/i }),
    ).not.toBeInTheDocument();
  });

  it("renders the assign button when permitted and status is not terminal-inactive", () => {
    renderSection({ status: "draft" });

    expect(
      screen.getByRole("button", { name: /assign owner/i }),
    ).toBeInTheDocument();
  });

  it("blocks submit with a field error when the owner reference is blank", async () => {
    const user = userEvent.setup();
    const { onAssign } = renderSection({ open: true });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/display name/i),
      "Site Safety Team",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /assign owner/i }),
    );

    expect(
      within(dialog).getByText("Owner reference is required"),
    ).toBeInTheDocument();
    expect(onAssign).not.toHaveBeenCalled();
  });
});

describe("ownerFormValuesToRequest", () => {
  it("builds the assign-owner request body with trimmed values", () => {
    const request = ownerFormValuesToRequest(
      {
        ownerType: "role",
        ownerReference: "  role:site-safety-lead  ",
        displayName: "  Site Safety Lead  ",
        reason: "  Reassigned after reorg  ",
      },
      5,
    );

    expect(request).toEqual({
      expected_version: 5,
      owner: {
        owner_type: "role",
        owner_reference: "role:site-safety-lead",
        display_name_snapshot: "Site Safety Lead",
      },
      reason: "Reassigned after reorg",
    });
  });
});

const UPDATE_CAPABILITIES: RiskControlCapabilities = {
  ...BASE_CAPABILITIES,
  canUpdate: true,
};

function renderPlanSection(
  overrides: Partial<{
    capabilities: RiskControlCapabilities;
    status: string;
    ownerAssigned: boolean;
    open: boolean;
    onPlan: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onOpenChange = vi.fn();
  const onPlan = overrides.onPlan ?? vi.fn();
  render(
    <ImplementationPlanSection
      status={overrides.status ?? "draft"}
      ownerAssigned={overrides.ownerAssigned ?? true}
      version={3}
      verificationMethodRequirement="Existing method"
      capabilities={overrides.capabilities ?? UPDATE_CAPABILITIES}
      open={overrides.open ?? false}
      onOpenChange={onOpenChange}
      onPlan={onPlan}
    />,
  );
  return { onOpenChange, onPlan };
}

describe("ImplementationPlanSection", () => {
  it("does not render the plan button when the control has no owner", () => {
    renderPlanSection({ ownerAssigned: false });

    expect(
      screen.queryByRole("button", { name: /plan implementation/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("Assign an owner before planning implementation."),
    ).toBeInTheDocument();
  });

  it("does not render the plan button when status is planned", () => {
    renderPlanSection({ status: "planned" });

    expect(
      screen.queryByRole("button", { name: /plan implementation/i }),
    ).not.toBeInTheDocument();
  });

  it("renders the plan button when permitted, draft, and owner is assigned", () => {
    renderPlanSection();

    expect(
      screen.getByRole("button", { name: /plan implementation/i }),
    ).toBeInTheDocument();
  });

  it("blocks submit with a field error when a milestone has no title", async () => {
    const user = userEvent.setup();
    const { onPlan } = renderPlanSection({ open: true });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/target completion date/i),
      "2026-09-01",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /add milestone/i }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /plan implementation/i }),
    );

    expect(
      within(dialog).getByText("Milestone title is required"),
    ).toBeInTheDocument();
    expect(onPlan).not.toHaveBeenCalled();
  });
});

describe("planFormValuesToRequest", () => {
  it("includes expected_version and an ISO target_completion_date", () => {
    const request = planFormValuesToRequest(
      {
        targetStartDate: "2026-08-01",
        targetCompletionDate: "2026-09-01",
        implementationMethod: "Install guarding",
        resourceNotes: "",
        dependencies: [],
        evidenceRequirements: [],
        verificationMethodRequirement: "Visual inspection",
        milestones: [],
      },
      7,
    );

    expect(request.expected_version).toBe(7);
    expect(request.implementation.target_completion_date).toBe(
      "2026-09-01T00:00:00Z",
    );
  });
});

describe("buildImplementationFormSchema milestone validation", () => {
  it("rejects a milestone without a title", () => {
    const schema = buildImplementationFormSchema(true);
    const result = schema.safeParse({
      targetStartDate: "",
      targetCompletionDate: "2026-09-01",
      implementationMethod: "",
      resourceNotes: "",
      dependencies: [],
      evidenceRequirements: [],
      verificationMethodRequirement: "",
      milestones: [
        { title: "", description: "", dueDate: "", status: "pending" },
      ],
    });

    expect(result.success).toBe(false);
  });
});

describe("buildImplementationFormSchema verificationMethodRequirement conditional validation", () => {
  const baseValues = {
    targetStartDate: "",
    targetCompletionDate: "2026-09-01",
    implementationMethod: "",
    resourceNotes: "",
    dependencies: [],
    evidenceRequirements: [],
    milestones: [],
  };

  it("allows a blank field when the control already has an existing value", () => {
    const schema = buildImplementationFormSchema(true);
    const result = schema.safeParse({
      ...baseValues,
      verificationMethodRequirement: "",
    });

    expect(result.success).toBe(true);
  });

  it("omits verification_method_requirement from the request when left blank with an existing value", () => {
    const request = planFormValuesToRequest(
      {
        ...baseValues,
        verificationMethodRequirement: "",
      },
      3,
    );

    expect(request).not.toHaveProperty("verification_method_requirement");
  });

  it("rejects a blank field when the control has no existing value", () => {
    const schema = buildImplementationFormSchema(false);
    const result = schema.safeParse({
      ...baseValues,
      verificationMethodRequirement: "",
    });

    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((candidate) =>
        candidate.path.includes("verificationMethodRequirement"),
      );
      expect(issue?.message).toBe(
        "Verification method requirement is required",
      );
    }
  });

  it("accepts a non-blank field when the control has no existing value", () => {
    const schema = buildImplementationFormSchema(false);
    const result = schema.safeParse({
      ...baseValues,
      verificationMethodRequirement: "Visual inspection",
    });

    expect(result.success).toBe(true);
  });
});

const IMPLEMENT_CAPABILITIES: RiskControlCapabilities = {
  ...BASE_CAPABILITIES,
  canImplement: true,
};

function buildMilestone(
  overrides: Partial<RiskControlMilestone> = {},
): RiskControlMilestone {
  return {
    id: "milestone-1",
    title: "Install guarding",
    description: "",
    dueDate: null,
    status: "pending",
    completedAt: null,
    evidenceRefs: [],
    ...overrides,
  };
}

function buildControl(overrides: Partial<RiskControl> = {}): RiskControl {
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
    status: "planned",
    latestEffectivenessResult: null,
    nextReviewDate: null,
    isOverdue: false,
    verificationMethodRequirement: "Visual inspection",
    version: 4,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderProgressSection(
  overrides: Partial<{
    control: RiskControl;
    capabilities: RiskControlCapabilities;
    startOpen: boolean;
    progressOpen: boolean;
    completeOpen: boolean;
    onStart: () => void | Promise<void>;
    onProgress: (values: unknown) => void | Promise<void>;
    onComplete: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onStartOpenChange = vi.fn();
  const onProgressOpenChange = vi.fn();
  const onCompleteOpenChange = vi.fn();
  const onStart = overrides.onStart ?? vi.fn();
  const onProgress = overrides.onProgress ?? vi.fn();
  const onComplete = overrides.onComplete ?? vi.fn();
  render(
    <ImplementationProgressSection
      control={overrides.control ?? buildControl()}
      capabilities={overrides.capabilities ?? IMPLEMENT_CAPABILITIES}
      startOpen={overrides.startOpen ?? false}
      onStartOpenChange={onStartOpenChange}
      progressOpen={overrides.progressOpen ?? false}
      onProgressOpenChange={onProgressOpenChange}
      completeOpen={overrides.completeOpen ?? false}
      onCompleteOpenChange={onCompleteOpenChange}
      onStart={onStart}
      onProgress={onProgress}
      onComplete={onComplete}
    />,
  );
  return {
    onStartOpenChange,
    onProgressOpenChange,
    onCompleteOpenChange,
    onStart,
    onProgress,
    onComplete,
  };
}

describe("ImplementationProgressSection", () => {
  it("shows the start button only when status is planned", () => {
    renderProgressSection({ control: buildControl({ status: "planned" }) });
    expect(
      screen.getByRole("button", { name: /start implementation/i }),
    ).toBeInTheDocument();

    cleanup();

    renderProgressSection({ control: buildControl({ status: "draft" }) });
    expect(
      screen.queryByRole("button", { name: /start implementation/i }),
    ).not.toBeInTheDocument();
  });

  it("shows the progress and complete buttons only when status is in_implementation", () => {
    renderProgressSection({
      control: buildControl({ status: "in_implementation" }),
    });
    expect(
      screen.getByRole("button", { name: /update progress/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /complete implementation/i }),
    ).toBeInTheDocument();

    cleanup();

    renderProgressSection({ control: buildControl({ status: "planned" }) });
    expect(
      screen.queryByRole("button", { name: /update progress/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /complete implementation/i }),
    ).not.toBeInTheDocument();
  });

  it("requires the evidence waiver reason exactly when evidence is empty", async () => {
    const user = userEvent.setup();
    const { onComplete } = renderProgressSection({
      control: buildControl({ status: "in_implementation", evidence: [] }),
      completeOpen: true,
    });

    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByLabelText(/evidence waiver reason/i),
    ).toBeInTheDocument();

    await user.type(
      within(dialog).getByLabelText(/completion summary/i),
      "Guarding installed and verified in the field",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /complete implementation/i }),
    );

    expect(
      within(dialog).getByText("Evidence waiver reason is required"),
    ).toBeInTheDocument();
    expect(onComplete).not.toHaveBeenCalled();
  });

  it("hides the evidence waiver reason field when evidence exists", () => {
    const control = buildControl({
      status: "in_implementation",
      evidence: [
        {
          id: "evidence-1",
          evidenceType: "photo",
          externalReference: "ref-1",
          title: "Guard installed photo",
          description: "",
          capturedAt: null,
          capturedByUserId: null,
          checksum: null,
          metadata: {},
        },
      ],
    });
    renderProgressSection({ control, completeOpen: true });

    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).queryByLabelText(/evidence waiver reason/i),
    ).not.toBeInTheDocument();
  });

  it("shows the incomplete-milestones checkbox only when a milestone is pending", () => {
    const withPendingMilestone = buildControl({
      status: "in_implementation",
      implementation: {
        ...buildControl().implementation,
        milestones: [buildMilestone({ status: "pending" })],
      },
    });
    renderProgressSection({ control: withPendingMilestone, completeOpen: true });
    expect(
      screen.getByRole("checkbox", { name: /allow incomplete milestones/i }),
    ).toBeInTheDocument();

    cleanup();

    const withOnlyResolvedMilestones = buildControl({
      status: "in_implementation",
      implementation: {
        ...buildControl().implementation,
        milestones: [
          buildMilestone({ id: "m1", status: "completed" }),
          buildMilestone({ id: "m2", status: "cancelled" }),
        ],
      },
    });
    renderProgressSection({
      control: withOnlyResolvedMilestones,
      completeOpen: true,
    });
    expect(
      screen.queryByRole("checkbox", { name: /allow incomplete milestones/i }),
    ).not.toBeInTheDocument();
  });
});

describe("progressFormSchema", () => {
  it("rejects progress values outside 0-100", () => {
    expect(
      progressFormSchema.safeParse({ progress: 101, summary: "" }).success,
    ).toBe(false);
    expect(
      progressFormSchema.safeParse({ progress: -1, summary: "" }).success,
    ).toBe(false);
    expect(
      progressFormSchema.safeParse({ progress: 50, summary: "" }).success,
    ).toBe(true);
  });
});

describe("progressFormValuesToRequest", () => {
  it("carries expected_version in the request body", () => {
    const request = progressFormValuesToRequest(
      { progress: 42, summary: "Halfway there" },
      6,
    );

    expect(request).toEqual({
      expected_version: 6,
      progress: 42,
      summary: "Halfway there",
    });
  });
});

describe("buildCompleteImplementationFormSchema", () => {
  it("requires evidenceWaiverReason only when evidence is empty", () => {
    const requiredSchema = buildCompleteImplementationFormSchema(true);
    expect(
      requiredSchema.safeParse({
        summary: "Done",
        evidenceWaiverReason: "",
        allowIncompleteMilestones: false,
      }).success,
    ).toBe(false);

    const optionalSchema = buildCompleteImplementationFormSchema(false);
    expect(
      optionalSchema.safeParse({
        summary: "Done",
        evidenceWaiverReason: "",
        allowIncompleteMilestones: false,
      }).success,
    ).toBe(true);
  });
});

describe("completeImplementationFormValuesToRequest", () => {
  it("carries expected_version and includes the waiver reason only when evidence is empty", () => {
    const withWaiver = completeImplementationFormValuesToRequest(
      {
        summary: "Guarding installed",
        evidenceWaiverReason: "Photo evidence pending upload",
        allowIncompleteMilestones: true,
      },
      9,
      true,
    );
    expect(withWaiver).toEqual({
      expected_version: 9,
      summary: "Guarding installed",
      evidence_waiver_reason: "Photo evidence pending upload",
      allow_incomplete_milestones: true,
    });

    const withoutWaiver = completeImplementationFormValuesToRequest(
      {
        summary: "Guarding installed",
        evidenceWaiverReason: "",
        allowIncompleteMilestones: false,
      },
      9,
      false,
    );
    expect(withoutWaiver).toEqual({
      expected_version: 9,
      summary: "Guarding installed",
    });
  });
});

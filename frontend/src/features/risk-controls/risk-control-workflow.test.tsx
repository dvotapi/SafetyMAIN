import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/feedback/Toast";
import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { EvidenceForm } from "@/features/risk-controls/components/evidence-form";
import { ImplementationPlanSection } from "@/features/risk-controls/components/implementation-plan-section";
import { ImplementationProgressSection } from "@/features/risk-controls/components/implementation-progress-section";
import { EffectivenessSummary } from "@/features/risk-controls/components/effectiveness-summary";
import { ReviewScheduleSection } from "@/features/risk-controls/components/review-schedule-section";
import { RiskControlLifecycleActions } from "@/features/risk-controls/components/risk-control-lifecycle-actions";
import { VerificationForm } from "@/features/risk-controls/components/verification-form";
import { VerificationHistory } from "@/features/risk-controls/components/verification-history";
import { completeRiskControlReview } from "@/features/risk-controls/api/risk-control-commands";
import {
  buildEvidenceFormSchema,
  evidenceFormValuesToRequest,
} from "@/features/risk-controls/schemas/evidence-schema";
import {
  reasonOnlyFormValuesToRequest,
  supersedeFormSchema,
  supersedeFormValuesToRequest,
  suspendFormSchema,
  suspendFormValuesToRequest,
} from "@/features/risk-controls/schemas/lifecycle-command-schema";
import {
  buildVerificationFormSchema,
  verificationFormValuesToRequest,
} from "@/features/risk-controls/schemas/verification-schema";
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
import { RiskControlObjectPage } from "@/features/risk-controls/pages/risk-control-object-page";
import { ownerFormValuesToRequest } from "@/features/risk-controls/schemas/owner-schema";
import {
  DEFAULT_COMPLETE_REVIEW_FORM_VALUES,
  buildCompleteReviewFormSchema,
  completeReviewFormValuesToRequest,
  reviewScheduleFormSchema,
  reviewScheduleFormValuesToRequest,
  type CompleteReviewFormValues,
} from "@/features/risk-controls/schemas/review-schema";
import type { RiskControlDto } from "@/features/risk-controls/types/risk-control-dto";
import type {
  RiskControl,
  RiskControlCapabilities,
  RiskControlLifecycleAction,
  RiskControlMilestone,
  RiskControlReviewSchedule,
  RiskControlVerification,
} from "@/features/risk-controls/types/risk-control-types";
import { apiClient } from "@/services/api/client";

// Used only by the RiskControlObjectPage render test below — grants every
// permission so capability gating never hides the Complete review button,
// and pins a stable organizationId so the query and mutation hooks (which
// both key their cache entries off it) stay in sync.
vi.mock("@/hooks/auth", () => ({
  useAuth: () => ({ hasPermission: () => true }),
  useOrganization: () => ({
    organizationId: "org-1",
    organizationName: "Org",
    membership: null,
  }),
}));

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
    renderProgressSection({
      control: withPendingMilestone,
      completeOpen: true,
    });
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

function renderEvidenceForm(
  overrides: Partial<{
    status: string;
    open: boolean;
    onSubmit: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onOpenChange = vi.fn();
  const onSubmit = overrides.onSubmit ?? vi.fn();
  render(
    <EvidenceForm
      status={overrides.status ?? "planned"}
      version={4}
      open={overrides.open ?? true}
      onOpenChange={onOpenChange}
      onSubmit={onSubmit}
    />,
  );
  return { onOpenChange, onSubmit };
}

describe("EvidenceForm", () => {
  it("never offers binary evidence upload", () => {
    const { container } = render(
      <EvidenceForm
        status="planned"
        version={4}
        open
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });

  it("shows the allow-after-implemented checkbox only in implemented/verified states", async () => {
    renderEvidenceForm({ status: "in_implementation" });
    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).queryByLabelText(/add evidence after implementation/i),
    ).not.toBeInTheDocument();
    cleanup();

    for (const status of [
      "implemented",
      "verified_effective",
      "verified_ineffective",
    ]) {
      renderEvidenceForm({ status });
      const implementedDialog = await screen.findByRole("dialog");
      expect(
        within(implementedDialog).getByLabelText(
          /add evidence after implementation/i,
        ),
      ).toBeInTheDocument();
      expect(
        within(implementedDialog).getByText(
          "This control is already implemented. Adding evidence now is an explicit append to the record.",
        ),
      ).toBeInTheDocument();
      cleanup();
    }
  });

  it("blocks submit until allow-after-implemented is checked", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderEvidenceForm({ status: "implemented" });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/external reference/i),
      "DOC-123",
    );
    await user.type(within(dialog).getByLabelText(/title/i), "Install photo");
    await user.click(
      within(dialog).getByRole("button", { name: /add evidence/i }),
    );

    expect(onSubmit).not.toHaveBeenCalled();

    await user.click(
      within(dialog).getByLabelText(/add evidence after implementation/i),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /add evidence/i }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ allowAfterImplemented: true }),
    );
  });

  it("blocks submit with a field error when the external reference is blank", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderEvidenceForm();

    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText(/title/i), "Install photo");
    await user.click(
      within(dialog).getByRole("button", { name: /add evidence/i }),
    );

    expect(
      within(dialog).getByText("External reference is required"),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe("buildEvidenceFormSchema", () => {
  const baseValues = {
    evidenceType: "document" as const,
    externalReference: "DOC-123",
    title: "Install photo",
    description: "",
    checksum: "",
    allowAfterImplemented: false,
  };

  it("requires allowAfterImplemented only when the control is post-implementation", () => {
    const requiredSchema = buildEvidenceFormSchema(true);
    expect(requiredSchema.safeParse(baseValues).success).toBe(false);
    expect(
      requiredSchema.safeParse({ ...baseValues, allowAfterImplemented: true })
        .success,
    ).toBe(true);

    const optionalSchema = buildEvidenceFormSchema(false);
    expect(optionalSchema.safeParse(baseValues).success).toBe(true);
  });
});

describe("evidenceFormValuesToRequest", () => {
  it("carries expected_version and omits optional blank fields", () => {
    const request = evidenceFormValuesToRequest(
      {
        evidenceType: "document",
        externalReference: "DOC-123",
        title: "Install photo",
        description: "",
        checksum: "",
        allowAfterImplemented: false,
      },
      6,
    );
    expect(request).toEqual({
      expected_version: 6,
      evidence_type: "document",
      external_reference: "DOC-123",
      title: "Install photo",
    });
  });

  it("includes description, checksum, and allow_after_implemented when set", () => {
    const request = evidenceFormValuesToRequest(
      {
        evidenceType: "photo",
        externalReference: "DOC-124",
        title: "Guarding photo",
        description: "Post-installation photo",
        checksum: "sha256:abc123",
        allowAfterImplemented: true,
      },
      7,
    );
    expect(request).toEqual({
      expected_version: 7,
      evidence_type: "photo",
      external_reference: "DOC-124",
      title: "Guarding photo",
      description: "Post-installation photo",
      checksum: "sha256:abc123",
      allow_after_implemented: true,
    });
  });
});

const VERIFY_CAPABILITIES: RiskControlCapabilities = {
  ...BASE_CAPABILITIES,
  canVerify: true,
};

function renderVerificationForm(
  overrides: Partial<{
    status: string;
    capabilities: RiskControlCapabilities;
    reviewRequired: boolean;
    noReviewReason: string | null;
    hasExistingEvidence: boolean;
    open: boolean;
    onSubmit: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onOpenChange = vi.fn();
  const onSubmit = overrides.onSubmit ?? vi.fn();
  render(
    <VerificationForm
      status={overrides.status ?? "implemented"}
      capabilities={overrides.capabilities ?? VERIFY_CAPABILITIES}
      reviewRequired={overrides.reviewRequired ?? true}
      noReviewReason={overrides.noReviewReason ?? null}
      hasExistingEvidence={overrides.hasExistingEvidence ?? true}
      version={4}
      open={overrides.open ?? false}
      onOpenChange={onOpenChange}
      onSubmit={onSubmit}
    />,
  );
  return { onOpenChange, onSubmit };
}

describe("VerificationForm availability", () => {
  it("does not render the record-verification button without risk_control:verify", () => {
    renderVerificationForm({ capabilities: BASE_CAPABILITIES });
    expect(
      screen.queryByRole("button", { name: /record verification/i }),
    ).not.toBeInTheDocument();
  });

  it("does not render when status is draft", () => {
    renderVerificationForm({ status: "draft" });
    expect(
      screen.queryByRole("button", { name: /record verification/i }),
    ).not.toBeInTheDocument();
  });

  it("renders when permitted and status is implemented", () => {
    renderVerificationForm({ status: "implemented" });
    expect(
      screen.getByRole("button", { name: /record verification/i }),
    ).toBeInTheDocument();
  });

  it("renders when status is verified_effective or verified_ineffective", () => {
    renderVerificationForm({ status: "verified_effective" });
    expect(
      screen.getByRole("button", { name: /record verification/i }),
    ).toBeInTheDocument();

    cleanup();

    renderVerificationForm({ status: "verified_ineffective" });
    expect(
      screen.getByRole("button", { name: /record verification/i }),
    ).toBeInTheDocument();
  });
});

describe("VerificationForm result options", () => {
  it("offers only the three verifiable results, each with a visible text label", async () => {
    renderVerificationForm({ open: true });
    const dialog = await screen.findByRole("dialog");

    expect(
      within(dialog).getByRole("radio", { name: "Verified Effective" }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("radio", {
        name: "Verified Partially Effective",
      }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByRole("radio", { name: "Verified Ineffective" }),
    ).toBeInTheDocument();
    expect(
      within(dialog).queryByRole("radio", { name: /not verified/i }),
    ).not.toBeInTheDocument();
    expect(
      within(dialog).queryByRole("radio", { name: /not applicable/i }),
    ).not.toBeInTheDocument();
  });
});

describe("VerificationForm submit validation", () => {
  it("blocks submit for effective without a next review date when review is required", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderVerificationForm({
      open: true,
      reviewRequired: true,
      noReviewReason: null,
      hasExistingEvidence: true,
    });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/method/i),
      "Field inspection",
    );
    await user.click(
      within(dialog).getByRole("radio", { name: "Verified Effective" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /record verification/i }),
    );

    expect(
      within(dialog).getByText(
        "A next review date is required when verifying a control effective.",
      ),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("allows submit for effective without a next review date when review is not required", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderVerificationForm({
      open: true,
      reviewRequired: false,
      hasExistingEvidence: true,
    });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/method/i),
      "Field inspection",
    );
    await user.click(
      within(dialog).getByRole("radio", { name: "Verified Effective" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /record verification/i }),
    );

    expect(onSubmit).toHaveBeenCalled();
  });

  it("blocks submit when evidenceRefs is empty and the control has no existing evidence", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderVerificationForm({
      open: true,
      reviewRequired: false,
      hasExistingEvidence: false,
    });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/method/i),
      "Field inspection",
    );
    await user.click(
      within(dialog).getByRole("radio", { name: "Verified Ineffective" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /record verification/i }),
    );

    expect(
      within(dialog).getByText("At least one evidence reference is required."),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("allows empty evidenceRefs when the control already has evidence", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderVerificationForm({
      open: true,
      reviewRequired: false,
      hasExistingEvidence: true,
    });

    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/method/i),
      "Field inspection",
    );
    await user.click(
      within(dialog).getByRole("radio", { name: "Verified Ineffective" }),
    );
    await user.click(
      within(dialog).getByRole("button", { name: /record verification/i }),
    );

    expect(onSubmit).toHaveBeenCalled();
  });
});

describe("buildVerificationFormSchema", () => {
  const base = {
    verificationType: "initial" as const,
    method: "Field inspection",
    criteria: "",
    result: "effective" as const,
    rating: "",
    findings: "",
    evidenceRefs: ["EV-1"],
    nextAction: "",
    nextReviewDate: "",
  };

  it("requires nextReviewDate for effective only when review is required and no reason is on file", () => {
    expect(
      buildVerificationFormSchema({
        reviewRequired: true,
        noReviewReason: null,
        hasExistingEvidence: true,
      }).safeParse(base).success,
    ).toBe(false);

    expect(
      buildVerificationFormSchema({
        reviewRequired: true,
        noReviewReason: "Control line retired next quarter",
        hasExistingEvidence: true,
      }).safeParse(base).success,
    ).toBe(true);

    expect(
      buildVerificationFormSchema({
        reviewRequired: false,
        noReviewReason: null,
        hasExistingEvidence: true,
      }).safeParse(base).success,
    ).toBe(true);
  });

  it("allows empty evidenceRefs only when the control already has evidence", () => {
    const ineffective = {
      ...base,
      result: "ineffective" as const,
      evidenceRefs: [],
    };

    expect(
      buildVerificationFormSchema({
        reviewRequired: false,
        noReviewReason: null,
        hasExistingEvidence: false,
      }).safeParse(ineffective).success,
    ).toBe(false);

    expect(
      buildVerificationFormSchema({
        reviewRequired: false,
        noReviewReason: null,
        hasExistingEvidence: true,
      }).safeParse(ineffective).success,
    ).toBe(true);
  });

  it("never accepts not_verified or not_applicable as a result", () => {
    const schema = buildVerificationFormSchema({
      reviewRequired: false,
      noReviewReason: null,
      hasExistingEvidence: true,
    });

    expect(schema.safeParse({ ...base, result: "not_verified" }).success).toBe(
      false,
    );
    expect(
      schema.safeParse({ ...base, result: "not_applicable" }).success,
    ).toBe(false);
  });
});

describe("verificationFormValuesToRequest", () => {
  it("carries expected_version and sends profile_key/profile_version explicitly", () => {
    const request = verificationFormValuesToRequest(
      {
        verificationType: "initial",
        method: "Field inspection",
        criteria: "",
        result: "effective",
        rating: "",
        findings: "",
        evidenceRefs: [],
        nextAction: "",
        nextReviewDate: "2026-09-01",
      },
      8,
    );

    expect(request).toEqual({
      expected_version: 8,
      verification_type: "initial",
      method: "Field inspection",
      result: "effective",
      evidence_refs: [],
      next_review_date: "2026-09-01T00:00:00Z",
      profile_key: "default",
      profile_version: "1",
    });
  });
});

function buildVerification(
  overrides: Partial<RiskControlVerification> = {},
): RiskControlVerification {
  return {
    id: "verification-1",
    verificationType: "initial",
    method: "Field inspection",
    criteria: "",
    performedAt: "2026-08-01T00:00:00Z",
    performedByUserId: "user-1",
    result: "partially_effective",
    rating: null,
    findings: "",
    evidenceRefs: [],
    nextAction: null,
    nextReviewDate: null,
    profileKey: "default",
    profileVersion: "1",
    ...overrides,
  };
}

describe("partially_effective never collapses into effective or ineffective", () => {
  it("never renders 'Verified Effective' or 'Verified Ineffective' anywhere when the latest result is partially_effective", () => {
    const verification = buildVerification({ result: "partially_effective" });
    const { container } = render(
      <>
        <EffectivenessSummary
          latestResult="partially_effective"
          latestVerification={verification}
          riskAssessmentId={null}
        />
        <VerificationHistory verifications={[verification]} />
      </>,
    );

    expect(container.textContent).toContain("Verified Partially Effective");
    expect(container.textContent).not.toContain("Verified Effective");
    expect(container.textContent).not.toContain("Verified Ineffective");
  });
});

describe("VerificationHistory is append-only", () => {
  it("never renders an edit/delete/remove control for any record, including the latest", () => {
    const verifications: RiskControlVerification[] = [
      buildVerification({
        id: "v1",
        result: "ineffective",
        performedAt: "2026-06-01T00:00:00Z",
      }),
      buildVerification({
        id: "v2",
        result: "partially_effective",
        performedAt: "2026-07-01T00:00:00Z",
      }),
      buildVerification({
        id: "v3",
        result: "effective",
        performedAt: "2026-08-01T00:00:00Z",
      }),
    ];

    render(<VerificationHistory verifications={verifications} />);

    expect(
      screen.queryAllByRole("button", { name: /edit|delete|remove/i }),
    ).toHaveLength(0);
    expect(
      screen.queryAllByRole("link", { name: /edit|delete|remove/i }),
    ).toHaveLength(0);
    expect(screen.getAllByText("Latest")).toHaveLength(1);
  });
});

/* ----------------------------------------------------------------------
 * Task B8: review scheduling, review completion, overdue presentation.
 * ---------------------------------------------------------------------- */

const REVIEW_CAPABILITIES: RiskControlCapabilities = {
  ...BASE_CAPABILITIES,
  canReview: true,
};

function buildReviewSchedule(
  overrides: Partial<RiskControlReviewSchedule> = {},
): RiskControlReviewSchedule {
  return {
    reviewRequired: true,
    reviewFrequencyDays: 365,
    nextReviewDate: "2026-09-01T00:00:00Z",
    lastReviewDate: null,
    reviewBasis: "fixed_interval",
    escalationPolicyRef: null,
    noReviewReason: null,
    ...overrides,
  };
}

function renderReviewSection(
  overrides: Partial<{
    capabilities: RiskControlCapabilities;
    status: string;
    reviewSchedule: RiskControlReviewSchedule;
    isOverdue: boolean;
    scheduleOpen: boolean;
    completeOpen: boolean;
    onSchedule: (values: unknown) => void | Promise<void>;
    onComplete: (values: unknown) => void | Promise<void>;
  }> = {},
) {
  const onScheduleOpenChange = vi.fn();
  const onCompleteOpenChange = vi.fn();
  const onSchedule = overrides.onSchedule ?? vi.fn();
  const onComplete = overrides.onComplete ?? vi.fn();
  render(
    <ReviewScheduleSection
      reviewSchedule={overrides.reviewSchedule ?? buildReviewSchedule()}
      status={overrides.status ?? "implemented"}
      version={5}
      isOverdue={overrides.isOverdue ?? false}
      capabilities={overrides.capabilities ?? REVIEW_CAPABILITIES}
      hasExistingEvidence
      scheduleOpen={overrides.scheduleOpen ?? false}
      onScheduleOpenChange={onScheduleOpenChange}
      completeOpen={overrides.completeOpen ?? false}
      onCompleteOpenChange={onCompleteOpenChange}
      onSchedule={onSchedule}
      onComplete={onComplete}
    />,
  );
  return {
    onScheduleOpenChange,
    onCompleteOpenChange,
    onSchedule,
    onComplete,
  };
}

describe("ReviewScheduleSection availability", () => {
  it("does not render Schedule review without risk_control:review", () => {
    renderReviewSection({
      capabilities: { ...REVIEW_CAPABILITIES, canReview: false },
    });

    expect(
      screen.queryByRole("button", { name: /schedule review/i }),
    ).not.toBeInTheDocument();
  });

  it("does not render Schedule review when status is terminal-inactive", () => {
    renderReviewSection({ status: "archived" });

    expect(
      screen.queryByRole("button", { name: /schedule review/i }),
    ).not.toBeInTheDocument();
  });

  it("renders Schedule review when permitted and status is not terminal-inactive", () => {
    renderReviewSection({ status: "implemented" });

    expect(
      screen.getByRole("button", { name: /schedule review/i }),
    ).toBeInTheDocument();
  });

  it("does not render Complete review when review is not required", () => {
    renderReviewSection({
      reviewSchedule: buildReviewSchedule({ reviewRequired: false }),
    });

    expect(
      screen.queryByRole("button", { name: /complete review/i }),
    ).not.toBeInTheDocument();
  });

  it("does not render Complete review when there is no next review date", () => {
    renderReviewSection({
      reviewSchedule: buildReviewSchedule({ nextReviewDate: null }),
    });

    expect(
      screen.queryByRole("button", { name: /complete review/i }),
    ).not.toBeInTheDocument();
  });

  it("renders Complete review when permitted, review is required, and a next review date exists", () => {
    renderReviewSection();

    expect(
      screen.getByRole("button", { name: /complete review/i }),
    ).toBeInTheDocument();
  });
});

describe("ReviewScheduleSection overdue presentation keys off isOverdue only", () => {
  it("renders the overdue banner with the exact copy when isOverdue is true", () => {
    renderReviewSection({ isOverdue: true });

    expect(screen.getByText("Review overdue")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The scheduled review date has passed. Complete the review to bring this control back into compliance.",
      ),
    ).toBeInTheDocument();
  });

  it("renders no overdue indicator when isOverdue is false, even with a past next review date", () => {
    renderReviewSection({
      isOverdue: false,
      reviewSchedule: buildReviewSchedule({
        // Past date, but the control is e.g. suspended — the domain never
        // marks a suspended control overdue, and the frontend must not
        // second-guess that by comparing dates itself.
        nextReviewDate: "2020-01-01T00:00:00Z",
      }),
    });

    expect(screen.queryByText("Review overdue")).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        "The scheduled review date has passed. Complete the review to bring this control back into compliance.",
      ),
    ).not.toBeInTheDocument();
  });
});

describe("reviewScheduleFormSchema", () => {
  const base = {
    reviewRequired: true,
    reviewFrequencyDays: 365,
    nextReviewDate: "",
    reviewBasis: "fixed_interval" as const,
    escalationPolicyRef: "",
    noReviewReason: "",
  };

  it("requires noReviewReason when reviewRequired is false", () => {
    expect(
      reviewScheduleFormSchema.safeParse({
        ...base,
        reviewRequired: false,
        noReviewReason: "",
      }).success,
    ).toBe(false);

    expect(
      reviewScheduleFormSchema.safeParse({
        ...base,
        reviewRequired: false,
        noReviewReason: "Control line retired next quarter",
      }).success,
    ).toBe(true);
  });

  it("requires reviewFrequencyDays when reviewRequired is true and nextReviewDate is empty", () => {
    expect(
      reviewScheduleFormSchema.safeParse({
        ...base,
        reviewFrequencyDays: null,
        nextReviewDate: "",
      }).success,
    ).toBe(false);

    expect(
      reviewScheduleFormSchema.safeParse({
        ...base,
        reviewFrequencyDays: null,
        nextReviewDate: "2026-09-01",
      }).success,
    ).toBe(true);

    expect(
      reviewScheduleFormSchema.safeParse({
        ...base,
        reviewFrequencyDays: 90,
        nextReviewDate: "",
      }).success,
    ).toBe(true);
  });
});

describe("reviewScheduleFormValuesToRequest", () => {
  it("carries expected_version and builds the nested schedule body", () => {
    const request = reviewScheduleFormValuesToRequest(
      {
        reviewRequired: true,
        reviewFrequencyDays: 180,
        nextReviewDate: "",
        reviewBasis: "risk_based",
        escalationPolicyRef: "  ESC-1  ",
        noReviewReason: "",
      },
      5,
    );

    expect(request).toEqual({
      expected_version: 5,
      schedule: {
        review_required: true,
        review_frequency_days: 180,
        next_review_date: null,
        review_basis: "risk_based",
        escalation_policy_ref: "ESC-1",
        no_review_reason: null,
      },
    });
  });

  it("sends no_review_reason and null frequency when review is not required", () => {
    const request = reviewScheduleFormValuesToRequest(
      {
        reviewRequired: false,
        reviewFrequencyDays: 180,
        nextReviewDate: "",
        reviewBasis: "manual",
        escalationPolicyRef: "",
        noReviewReason: "Control line retired next quarter",
      },
      5,
    );

    expect(request.schedule.review_required).toBe(false);
    expect(request.schedule.review_frequency_days).toBeNull();
    expect(request.schedule.no_review_reason).toBe(
      "Control line retired next quarter",
    );
  });
});

describe("buildCompleteReviewFormSchema", () => {
  const options = {
    reviewRequired: true,
    noReviewReason: null,
    hasExistingEvidence: false,
  };

  it("never validates the nested verification when includeVerification is false", () => {
    const values: CompleteReviewFormValues = {
      ...DEFAULT_COMPLETE_REVIEW_FORM_VALUES,
      includeVerification: false,
    };

    expect(
      buildCompleteReviewFormSchema(options).safeParse(values).success,
    ).toBe(true);
  });

  it("applies the same cross-field rules as the standalone verification form when includeVerification is true", () => {
    const values: CompleteReviewFormValues = {
      nextReviewDate: "",
      includeVerification: true,
      verification: {
        verificationType: "scheduled_review",
        method: "Field inspection",
        criteria: "",
        result: "ineffective",
        rating: "",
        findings: "",
        // hasExistingEvidence is false above, so an empty evidenceRefs
        // must fail — same rule as buildVerificationFormSchema.
        evidenceRefs: [],
        nextAction: "",
        nextReviewDate: "",
      },
    };

    const result = buildCompleteReviewFormSchema(options).safeParse(values);
    expect(result.success).toBe(false);
  });

  it("accepts a valid nested verification when includeVerification is true", () => {
    const values: CompleteReviewFormValues = {
      nextReviewDate: "",
      includeVerification: true,
      verification: {
        verificationType: "scheduled_review",
        method: "Field inspection",
        criteria: "",
        result: "ineffective",
        rating: "",
        findings: "",
        evidenceRefs: ["EV-1"],
        nextAction: "",
        nextReviewDate: "",
      },
    };

    expect(
      buildCompleteReviewFormSchema(options).safeParse(values).success,
    ).toBe(true);
  });
});

describe("completeReviewFormValuesToRequest", () => {
  it("omits verification entirely when includeVerification is false", () => {
    const request = completeReviewFormValuesToRequest(
      {
        nextReviewDate: "2026-09-01",
        includeVerification: false,
        verification: {
          verificationType: "initial",
          method: "",
          criteria: "",
          result: "effective",
          rating: "",
          findings: "",
          evidenceRefs: [],
          nextAction: "",
          nextReviewDate: "",
        },
      },
      5,
    );

    expect(request).toEqual({
      expected_version: 5,
      next_review_date: "2026-09-01T00:00:00Z",
    });
    expect(request).not.toHaveProperty("verification");
  });

  it("TRAP 1: sets the nested verification.expected_version to the control's current version, the same value as the top-level expected_version — never a separately computed value", () => {
    const request = completeReviewFormValuesToRequest(
      {
        nextReviewDate: "",
        includeVerification: true,
        verification: {
          verificationType: "scheduled_review",
          method: "Field inspection",
          criteria: "",
          result: "effective",
          rating: "",
          findings: "",
          evidenceRefs: ["EV-1"],
          nextAction: "",
          nextReviewDate: "2026-09-01",
        },
      },
      5,
    );

    expect(request.expected_version).toBe(5);
    expect(request.verification?.expected_version).toBe(5);
    expect(request.verification?.expected_version).toBe(
      request.expected_version,
    );
  });
});

function buildRiskControlDto(
  overrides: Partial<RiskControlDto> = {},
): RiskControlDto {
  return {
    id: "rc-1",
    organization_id: "org-1",
    code: "RC-1",
    title: "Conveyor guard rail",
    description: "Fixed guard on the conveyor pinch point",
    hierarchy_level: "engineering",
    control_nature: "preventive",
    source: { source_type: "manual" },
    hazard_id: null,
    risk_assessment_id: null,
    scope: [],
    owner: null,
    implementation: {},
    evidence: [],
    verifications: [],
    review_schedule: { review_required: true, review_frequency_days: 365 },
    competency_requirements: [],
    related_entities: [],
    extension_data: {},
    lifecycle_status: "implemented",
    latest_effectiveness_result: null,
    next_review_date: null,
    is_overdue: false,
    verification_method_requirement: "",
    version: 1,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("completeRiskControlReview version trap", () => {
  it("TRAP 2: a control at version 5 completing a review with a verification, receiving version 7 in the response, leaves the UI showing version 7 — never expected_version + 1", async () => {
    const responseDto = buildRiskControlDto({ version: 7 });
    const requestSpy = vi
      .spyOn(apiClient, "request")
      .mockResolvedValue(responseDto);

    const body = {
      expected_version: 5,
      verification: {
        expected_version: 5,
        method: "Field inspection",
        result: "effective" as const,
        evidence_refs: ["EV-1"],
        next_review_date: "2026-09-01T00:00:00Z",
      },
    };

    const result = await completeRiskControlReview("rc-1", body);

    expect(requestSpy).toHaveBeenCalledWith({
      method: "POST",
      path: "/api/v1/risk-controls/rc-1/complete-review",
      body,
    });
    // The response carries the double-bumped version (5 -> 6 for the
    // review completion, 6 -> 7 for the applied verification). The
    // mapped result must reflect that, never a client-computed 6.
    expect(result.version).toBe(7);
    expect(result.version).not.toBe(body.expected_version + 1);

    requestSpy.mockRestore();
  });
});

describe("RiskControlObjectPage renders the version the server returns (TRAP 2, end to end)", () => {
  it("shows Version 7 after completing a review with a verification that the server double-bumps, never a client-computed 6", async () => {
    const user = userEvent.setup();
    const detailDto = buildRiskControlDto({
      version: 5,
      lifecycle_status: "implemented",
      review_schedule: {
        review_required: true,
        review_frequency_days: 365,
        next_review_date: "2026-09-01T00:00:00Z",
      },
    });
    const completedDto = buildRiskControlDto({
      ...detailDto,
      version: 7,
    });

    const requestSpy = vi
      .spyOn(apiClient, "request")
      .mockImplementation(async (options) => {
        if (
          options.method === "GET" &&
          options.path === "/api/v1/risk-controls/rc-1"
        ) {
          return detailDto;
        }
        if (
          options.method === "POST" &&
          options.path === "/api/v1/risk-controls/rc-1/complete-review"
        ) {
          return completedDto;
        }
        throw new Error(
          `Unexpected request: ${options.method} ${options.path}`,
        );
      });

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <RiskControlObjectPage riskControlId="rc-1" />
        </ToastProvider>
      </QueryClientProvider>,
    );

    // Initial load reflects version 5 from the detail query.
    expect(await screen.findByText("Version 5")).toBeInTheDocument();

    await user.click(
      await screen.findByRole("button", { name: /complete review/i }),
    );
    const dialog = await screen.findByRole("dialog");
    await user.click(
      within(dialog).getByRole("button", { name: /complete review/i }),
    );

    // The mutation's onSuccess must feed the response straight into the
    // object page's rendered state (via the detail query cache) — not a
    // client-computed expected_version + 1, and not a stale cached prop.
    expect(await screen.findByText("Version 7")).toBeInTheDocument();
    expect(screen.queryByText("Version 6")).not.toBeInTheDocument();

    requestSpy.mockRestore();
  });
});

/* ----------------------------------------------------------------------
 * RiskControlLifecycleActions and its five terminal command dialogs
 * ---------------------------------------------------------------------- */

const FULL_CAPABILITIES: RiskControlCapabilities = {
  canRead: true,
  canCreate: true,
  canUpdate: true,
  canAssignOwner: true,
  canImplement: true,
  canVerify: true,
  canReview: true,
  canSuspend: true,
  canSupersede: true,
  canArchive: true,
  canCancel: true,
  canMaterialize: true,
  canViewHazard: true,
  canViewAssessment: true,
  canViewActivity: true,
};

function noop() {
  // intentionally empty — forward-action callbacks under test only assert
  // they were invoked, not what they do.
}

function renderLifecycleActions(
  overrides: Partial<{
    control: RiskControl;
    capabilities: RiskControlCapabilities;
    busyAction: RiskControlLifecycleAction | null;
    errorMessage: string | null;
    onPlan: () => void;
    onSuspend: (values: unknown) => Promise<boolean> | boolean;
    onResume: () => Promise<boolean> | boolean;
    onSupersede: (values: unknown) => Promise<boolean> | boolean;
    onCancel: (values: unknown) => Promise<boolean> | boolean;
    onArchive: (values: unknown) => Promise<boolean> | boolean;
  }> = {},
) {
  const onPlan = overrides.onPlan ?? vi.fn();
  const onSuspend = overrides.onSuspend ?? vi.fn(async () => true);
  const onResume = overrides.onResume ?? vi.fn(async () => true);
  const onSupersede = overrides.onSupersede ?? vi.fn(async () => true);
  const onCancel = overrides.onCancel ?? vi.fn(async () => true);
  const onArchive = overrides.onArchive ?? vi.fn(async () => true);

  render(
    <RiskControlLifecycleActions
      control={overrides.control ?? buildControl({ status: "implemented" })}
      capabilities={overrides.capabilities ?? FULL_CAPABILITIES}
      busyAction={overrides.busyAction ?? null}
      errorMessage={overrides.errorMessage ?? null}
      onPlan={onPlan}
      onStartImplementation={noop}
      onCompleteImplementation={noop}
      onVerify={noop}
      onScheduleReview={noop}
      onSuspend={onSuspend}
      onResume={onResume}
      onSupersede={onSupersede}
      onCancel={onCancel}
      onArchive={onArchive}
    />,
  );
  return { onPlan, onSuspend, onResume, onSupersede, onCancel, onArchive };
}

describe("RiskControlLifecycleActions", () => {
  it("shows the fallback panel text when no actions are available", () => {
    renderLifecycleActions({ control: buildControl({ status: "archived" }) });
    expect(
      screen.getByText(
        "No lifecycle actions are available for this control in its current state.",
      ),
    ).toBeInTheDocument();
  });

  it("delegates the plan action to the page-owned dialog instead of opening its own", async () => {
    const user = userEvent.setup();
    const owner = {
      ownerType: "user",
      ownerReference: "user-1",
      displayNameSnapshot: "Jane Doe",
      assignedAt: null,
      assignedBy: null,
      label: "Jane Doe",
    };
    const { onPlan } = renderLifecycleActions({
      control: buildControl({ status: "draft", owner }),
    });
    await user.click(
      screen.getByRole("button", { name: /plan implementation/i }),
    );
    expect(onPlan).toHaveBeenCalledTimes(1);
    // The click must never open a dialog of its own — plan has no form here.
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("requires a reason before confirming suspend", async () => {
    const user = userEvent.setup();
    const { onSuspend } = renderLifecycleActions({
      control: buildControl({ status: "implemented" }),
    });
    await user.click(screen.getByRole("button", { name: /suspend control/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(
      within(dialog).getByRole("button", { name: /suspend control/i }),
    );
    expect(onSuspend).not.toHaveBeenCalled();
    expect(within(dialog).getByText(/reason is required/i)).toBeInTheDocument();
  });

  it("submits suspend with the reason and optional resolution date", async () => {
    const user = userEvent.setup();
    const { onSuspend } = renderLifecycleActions({
      control: buildControl({ status: "implemented" }),
    });
    await user.click(screen.getByRole("button", { name: /suspend control/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/reason/i),
      "Waiting on parts",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /suspend control/i }),
    );
    expect(onSuspend).toHaveBeenCalledWith(
      expect.objectContaining({ reason: "Waiting on parts" }),
    );
  });

  it("offers resume with no form once suspended", async () => {
    const user = userEvent.setup();
    const { onResume } = renderLifecycleActions({
      control: buildControl({ status: "suspended" }),
    });
    await user.click(screen.getByRole("button", { name: /resume control/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(
      within(dialog).getByRole("button", { name: /resume control/i }),
    );
    expect(onResume).toHaveBeenCalledTimes(1);
  });

  it("rejects a non-UUID replacement control ID on supersede", async () => {
    const user = userEvent.setup();
    const { onSupersede } = renderLifecycleActions({
      control: buildControl({ status: "implemented" }),
    });
    await user.click(
      screen.getByRole("button", { name: /supersede control/i }),
    );
    const dialog = await screen.findByRole("dialog");
    await user.type(
      within(dialog).getByLabelText(/replacement control id/i),
      "not-a-uuid",
    );
    await user.type(within(dialog).getByLabelText(/reason/i), "Redesigned");
    await user.click(
      within(dialog).getByRole("button", { name: /supersede control/i }),
    );
    expect(onSupersede).not.toHaveBeenCalled();
    expect(within(dialog).getByText(/valid uuid/i)).toBeInTheDocument();
  });

  it("states the supersede copy verbatim and does not validate replacement existence", async () => {
    const user = userEvent.setup();
    const { onSupersede } = renderLifecycleActions({
      control: buildControl({ status: "implemented" }),
    });
    await user.click(
      screen.getByRole("button", { name: /supersede control/i }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText(
        "Superseding is not deletion — the control stays readable in its history.",
      ),
    ).toBeInTheDocument();
    const replacementId = "11111111-1111-4111-8111-111111111111";
    await user.type(
      within(dialog).getByLabelText(/replacement control id/i),
      replacementId,
    );
    await user.type(within(dialog).getByLabelText(/reason/i), "Redesigned");
    await user.click(
      within(dialog).getByRole("button", { name: /supersede control/i }),
    );
    expect(onSupersede).toHaveBeenCalledWith(
      expect.objectContaining({
        replacementControlId: replacementId,
        reason: "Redesigned",
      }),
    );
  });

  it("requires a reason before confirming cancel", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderLifecycleActions({
      control: buildControl({ status: "draft" }),
    });
    await user.click(screen.getByRole("button", { name: /cancel control/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(
      within(dialog).getByRole("button", { name: /cancel control/i }),
    );
    expect(onCancel).not.toHaveBeenCalled();
    await user.type(
      within(dialog).getByLabelText(/reason/i),
      "No longer needed",
    );
    await user.click(
      within(dialog).getByRole("button", { name: /cancel control/i }),
    );
    expect(onCancel).toHaveBeenCalledWith(
      expect.objectContaining({ reason: "No longer needed" }),
    );
  });

  it("states the archive copy verbatim and requires a reason", async () => {
    const user = userEvent.setup();
    const { onArchive } = renderLifecycleActions({
      control: buildControl({ status: "cancelled" }),
    });
    await user.click(screen.getByRole("button", { name: /archive control/i }));
    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText(
        "Archiving is not deletion. The control remains readable by direct link.",
      ),
    ).toBeInTheDocument();
    await user.click(
      within(dialog).getByRole("button", { name: /archive control/i }),
    );
    expect(onArchive).not.toHaveBeenCalled();
    await user.type(within(dialog).getByLabelText(/reason/i), "Retired");
    await user.click(
      within(dialog).getByRole("button", { name: /archive control/i }),
    );
    expect(onArchive).toHaveBeenCalledWith(
      expect.objectContaining({ reason: "Retired" }),
    );
  });

  it("disables every action button while any command is busy", () => {
    renderLifecycleActions({
      control: buildControl({ status: "implemented" }),
      busyAction: "verify",
    });
    for (const button of screen.getAllByRole("button")) {
      expect(button).toBeDisabled();
    }
  });
});

describe("suspendFormSchema", () => {
  it("rejects a blank reason", () => {
    const result = suspendFormSchema.safeParse({
      reason: "  ",
      expectedResolutionDate: "",
    });
    expect(result.success).toBe(false);
  });
});

describe("suspendFormValuesToRequest", () => {
  it("maps an empty resolution date to null and trims the reason", () => {
    const request = suspendFormValuesToRequest(
      { reason: "  Pending parts  ", expectedResolutionDate: "" },
      4,
    );
    expect(request).toEqual({
      expected_version: 4,
      reason: "Pending parts",
      expected_resolution_date: null,
    });
  });

  it("passes through a provided resolution date", () => {
    const request = suspendFormValuesToRequest(
      { reason: "Pending parts", expectedResolutionDate: "2026-09-01" },
      4,
    );
    expect(request.expected_resolution_date).toBe("2026-09-01");
  });
});

describe("supersedeFormSchema", () => {
  it("rejects a non-UUID replacement control ID", () => {
    const result = supersedeFormSchema.safeParse({
      replacementControlId: "not-a-uuid",
      reason: "Redesigned",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a valid UUID", () => {
    const result = supersedeFormSchema.safeParse({
      replacementControlId: "11111111-1111-4111-8111-111111111111",
      reason: "Redesigned",
    });
    expect(result.success).toBe(true);
  });
});

describe("supersedeFormValuesToRequest", () => {
  it("maps to SupersedeDto with the current version", () => {
    const request = supersedeFormValuesToRequest(
      {
        replacementControlId: "11111111-1111-4111-8111-111111111111",
        reason: "Redesigned",
      },
      6,
    );
    expect(request).toEqual({
      expected_version: 6,
      replacement_control_id: "11111111-1111-4111-8111-111111111111",
      reason: "Redesigned",
    });
  });
});

describe("reasonOnlyFormValuesToRequest", () => {
  it("maps to ReasonVersionDto shared by cancel and archive", () => {
    const request = reasonOnlyFormValuesToRequest(
      { reason: "  No longer needed  " },
      2,
    );
    expect(request).toEqual({
      expected_version: 2,
      reason: "No longer needed",
    });
  });
});

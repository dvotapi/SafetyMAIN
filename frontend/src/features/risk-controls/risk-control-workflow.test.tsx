import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
import { ImplementationPlanSection } from "@/features/risk-controls/components/implementation-plan-section";
import {
  buildImplementationFormSchema,
  planFormValuesToRequest,
} from "@/features/risk-controls/schemas/implementation-schema";
import { ownerFormValuesToRequest } from "@/features/risk-controls/schemas/owner-schema";
import type { RiskControlCapabilities } from "@/features/risk-controls/types/risk-control-types";

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

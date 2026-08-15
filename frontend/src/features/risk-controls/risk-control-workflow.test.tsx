import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ControlOwnerSection } from "@/features/risk-controls/components/control-owner-section";
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

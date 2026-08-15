import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RiskAssessmentLifecycleActions } from "@/features/risk-assessments/components/risk-assessment-lifecycle-actions";
import { mapRiskAssessmentCapabilities } from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import type { RiskAssessment } from "@/features/risk-assessments/types/risk-assessment-types";
import {
  prefillApproveAcceptance,
  toApproveAcceptanceInput,
  validateApproveAcceptance,
} from "@/features/risk-assessments/utils/approve-acceptance";

afterEach(() => {
  cleanup();
});

const capabilities = mapRiskAssessmentCapabilities(() => true);

function baseAssessment(
  overrides: Partial<RiskAssessment> = {},
): RiskAssessment {
  return {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    organizationId: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    hazardId: "cccccccc-cccc-cccc-cccc-cccccccccccc",
    code: "RA-1",
    title: "Approve dialog",
    assessmentProfile: "simple_3x3",
    assessedObject: { objectType: "workplace", reference: "Bay 1" },
    assessorId: "user-1",
    assessmentDate: "2026-08-01",
    reviewSchedule: {
      reviewDueDate: null,
      reviewFrequencyDays: null,
      reviewReason: null,
      triggeredBy: null,
    },
    inherentRisk: {
      level: "medium",
      factors: [
        { factor: "probability", score: 2 },
        { factor: "severity", score: 3 },
      ],
      explanation: "ok",
    },
    residualRisk: null,
    controls: [],
    acceptance: null,
    competencyRequirements: [],
    extensionReferences: {},
    status: "under_review",
    supersededById: null,
    archivedAt: null,
    archivedBy: null,
    approvedAt: null,
    approvedBy: null,
    createdAt: "2026-08-01T00:00:00Z",
    updatedAt: "2026-08-01T00:00:00Z",
    version: 2,
    ...overrides,
  };
}

describe("approve acceptance helpers", () => {
  it("prefills complete acceptance", () => {
    expect(
      prefillApproveAcceptance({
        decision: "accepted",
        justification: "Within tolerance",
        reviewerId: "rev-1",
        approvedAt: null,
      }),
    ).toEqual({
      decision: "accepted",
      justification: "Within tolerance",
    });
  });

  it("prefills incomplete acceptance so it can be corrected", () => {
    expect(
      prefillApproveAcceptance({
        decision: "accepted",
        justification: "",
        reviewerId: null,
        approvedAt: null,
      }),
    ).toEqual({
      decision: "accepted",
      justification: "",
    });
  });

  it("blocks accepted without justification client-side", () => {
    expect(
      validateApproveAcceptance({
        decision: "accepted",
        justification: "   ",
      }),
    ).toBe("Justification is required for accepted risks");
  });

  it("blocks conditionally_accepted without justification client-side", () => {
    expect(
      validateApproveAcceptance({
        decision: "conditionally_accepted",
        justification: "",
      }),
    ).toBe("Justification is required for accepted risks");
  });

  it("builds corrected acceptance payload", () => {
    expect(
      toApproveAcceptanceInput({
        decision: "accepted",
        justification: "  Corrected justification  ",
      }),
    ).toEqual({
      decision: "accepted",
      justification: "Corrected justification",
    });
  });
});

describe("RiskAssessmentLifecycleActions approve dialog", () => {
  it("lets the reviewer correct incomplete acceptance and sends the payload", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn(async () => true);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "accepted",
            justification: "",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={onApprove}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    expect(screen.getByLabelText(/Acceptance decision/i)).toBeInTheDocument();
    const justification = screen.getByLabelText(/Justification/i);
    expect(justification).toHaveValue("");

    await user.type(justification, "Now justified");
    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );

    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledWith({
        decision: "accepted",
        justification: "Now justified",
      });
    });
    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: "Approve assessment" }),
      ).not.toBeInTheDocument();
    });
  });

  it("prefills complete acceptance values", async () => {
    const user = userEvent.setup();

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "not_accepted",
            justification: "Escalate further",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={async () => true}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    expect(screen.getByLabelText(/Justification/i)).toHaveValue(
      "Escalate further",
    );
    // Decision select shows the formatted label for the current value.
    expect(screen.getByText("Not Accepted")).toBeInTheDocument();
  });

  it("blocks accepted without justification in the dialog", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn(async () => true);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "accepted",
            justification: "",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={onApprove}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    const approveButtons = screen.getAllByRole("button", {
      name: "Approve assessment",
    });
    await user.click(approveButtons[approveButtons.length - 1]!);

    expect(
      screen.getByText("Justification is required for accepted risks"),
    ).toBeInTheDocument();
    expect(onApprove).not.toHaveBeenCalled();
    expect(
      screen.getByRole("heading", { name: "Approve assessment" }),
    ).toBeInTheDocument();
  });

  it("blocks conditionally_accepted without justification in the dialog", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn(async () => true);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "conditionally_accepted",
            justification: "",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={onApprove}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    const approveButtons = screen.getAllByRole("button", {
      name: "Approve assessment",
    });
    await user.click(approveButtons[approveButtons.length - 1]!);

    expect(
      screen.getByText("Justification is required for accepted risks"),
    ).toBeInTheDocument();
    expect(onApprove).not.toHaveBeenCalled();
  });

  it("keeps the dialog open and preserves values when approval fails", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn(async () => false);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "accepted",
            justification: "",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={onApprove}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    await user.type(
      screen.getByLabelText(/Justification/i),
      "Will fail server-side",
    );
    const approveButtons = screen.getAllByRole("button", {
      name: "Approve assessment",
    });
    await user.click(approveButtons[approveButtons.length - 1]!);

    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledOnce();
    });
    expect(
      screen.getByRole("heading", { name: "Approve assessment" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Justification/i)).toHaveValue(
      "Will fail server-side",
    );
  });

  it("closes the dialog after successful approval", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn(async () => true);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment({
          acceptance: {
            decision: "requires_escalation",
            justification: "Need board",
            reviewerId: null,
            approvedAt: null,
          },
        })}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={onApprove}
        onArchive={async () => true}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Approve assessment" }),
    );
    const approveButtons = screen.getAllByRole("button", {
      name: "Approve assessment",
    });
    await user.click(approveButtons[approveButtons.length - 1]!);

    await waitFor(() => {
      expect(onApprove).toHaveBeenCalledWith({
        decision: "requires_escalation",
        justification: "Need board",
      });
    });
    await waitFor(() => {
      expect(
        screen.queryByRole("heading", { name: "Approve assessment" }),
      ).not.toBeInTheDocument();
    });
  });

  it("keeps the archive dialog open and preserves reason on failure", async () => {
    const user = userEvent.setup();
    const onArchive = vi.fn(async () => false);

    render(
      <RiskAssessmentLifecycleActions
        assessment={baseAssessment()}
        capabilities={capabilities}
        onSubmitForReview={async () => true}
        onApprove={async () => true}
        onArchive={onArchive}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Archive assessment" }),
    );
    await user.type(screen.getByLabelText(/Reason/i), "Duplicate scope");
    await user.click(
      screen.getByRole("button", { name: "Archive assessment" }),
    );

    await waitFor(() => {
      expect(onArchive).toHaveBeenCalledWith("Duplicate scope");
    });
    expect(
      screen.getByRole("heading", { name: "Archive assessment" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/Reason/i)).toHaveValue("Duplicate scope");
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components";
import {
  MaterializeControlsDialog,
  type MaterializableAssessmentStatus,
  type MaterializeProposedControl,
} from "@/features/risk-controls/components/materialize-controls-dialog";
import type { RiskControlDto } from "@/features/risk-controls/types/risk-control-dto";
import { apiClient } from "@/services/api/client";
import { ConflictError } from "@/services/api/errors";
import type { ApiRequestOptions } from "@/services/api/types";

let currentHasPermission: (permission: string) => boolean = () => true;

vi.mock("@/hooks/auth", () => ({
  useAuth: () => ({
    hasPermission: (permission: string) => currentHasPermission(permission),
  }),
  useOrganization: () => ({
    organizationId: "org-1",
    organizationName: "Org",
    membership: null,
  }),
}));

afterEach(() => {
  cleanup();
  currentHasPermission = () => true;
});

const PROPOSED_CONTROLS: MaterializeProposedControl[] = [
  {
    id: "ctrl-1",
    controlType: "administrative",
    description: "Lockout procedure",
  },
  {
    id: "ctrl-2",
    controlType: "ppe",
    description: "Hearing protection",
  },
];

function buildRiskControlDto(
  overrides: Partial<RiskControlDto> = {},
): RiskControlDto {
  return {
    id: "rc-1",
    organization_id: "org-1",
    code: "RC-0100",
    title: "Lockout procedure",
    description: "Lockout procedure",
    hierarchy_level: "administrative",
    control_nature: "preventive",
    source: { source_type: "manual" },
    hazard_id: null,
    risk_assessment_id: "ra-1",
    scope: [],
    owner: null,
    implementation: {},
    evidence: [],
    verifications: [],
    review_schedule: {},
    competency_requirements: [],
    related_entities: [],
    extension_data: {},
    lifecycle_status: "draft",
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

/** Default mock: empty related-controls list, no already-materialized items. */
function mockApiClient(
  handlers: Partial<{
    list: (options: ApiRequestOptions) => unknown;
    materialize: (options: ApiRequestOptions) => unknown;
  }> = {},
) {
  return vi.spyOn(apiClient, "request").mockImplementation(async (options) => {
    if (options.method === "GET" && options.path === "/api/v1/risk-controls") {
      return handlers.list
        ? handlers.list(options)
        : { items: [], pagination: { total: 0, offset: 0, limit: 100 } };
    }
    if (
      options.method === "POST" &&
      options.path === "/api/v1/risk-assessments/ra-1/materialize-controls"
    ) {
      return handlers.materialize
        ? handlers.materialize(options)
        : { items: [buildRiskControlDto()] };
    }
    throw new Error(`Unexpected request: ${options.method} ${options.path}`);
  });
}

function renderDialog(overrides: {
  assessmentStatus?: MaterializableAssessmentStatus;
  proposedControls?: MaterializeProposedControl[];
  open?: boolean;
} = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const onOpenChangeSpy = vi.fn();
  const onSuccess = vi.fn();

  function Host() {
    return (
      <MaterializeControlsDialog
        riskAssessmentId="ra-1"
        assessmentStatus={overrides.assessmentStatus ?? "approved"}
        proposedControls={overrides.proposedControls ?? PROPOSED_CONTROLS}
        open={overrides.open ?? true}
        onOpenChange={onOpenChangeSpy}
        onSuccess={onSuccess}
      />
    );
  }

  render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Host />
      </ToastProvider>
    </QueryClientProvider>,
  );

  return { onOpenChangeSpy, onSuccess };
}

describe("MaterializeControlsDialog availability", () => {
  it("does not render the trigger or dialog without risk_control:materialize", () => {
    currentHasPermission = (permission) =>
      permission !== "risk_control:materialize";
    mockApiClient();

    renderDialog();

    expect(
      screen.queryByRole("button", { name: /materialize controls/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});

describe("MaterializeControlsDialog status gating", () => {
  it("blocks a draft assessment with the exact BlockingReason copy and a disabled confirm button", async () => {
    mockApiClient();

    renderDialog({ assessmentStatus: "draft" });

    const dialog = await screen.findByRole("dialog");
    expect(
      screen.getByText(
        "Controls can only be materialized from an approved risk assessment.",
      ),
    ).toBeInTheDocument();
    expect(
      dialog.querySelector('[role="checkbox"]'),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^materialize$/i }),
    ).toBeDisabled();
  });
});

describe("MaterializeControlsDialog already-materialized entries", () => {
  it("shows a disabled checkbox with 'Already materialized' for a proposed control whose reference is already used", async () => {
    mockApiClient({
      list: () => ({
        items: [
          buildRiskControlDto({
            id: "rc-existing",
            source: {
              source_type: "risk_assessment",
              source_control_reference: "ctrl-1",
            },
          }),
        ],
        pagination: { total: 1, offset: 0, limit: 100 },
      }),
    });

    renderDialog({ assessmentStatus: "approved" });

    await screen.findByRole("dialog");

    const alreadyMaterialized = await screen.findByRole("checkbox", {
      name: /lockout procedure/i,
    });
    await waitFor(() => expect(alreadyMaterialized).toBeDisabled());
    expect(screen.getByText("Already materialized")).toBeInTheDocument();

    const selectable = screen.getByRole("checkbox", {
      name: /hearing protection/i,
    });
    expect(selectable).not.toBeDisabled();
  });
});

describe("MaterializeControlsDialog submission", () => {
  it("sends control_ids matching the selection and allow_under_review false for an approved assessment", async () => {
    const user = userEvent.setup();
    const requestSpy = mockApiClient();

    renderDialog({ assessmentStatus: "approved" });
    await screen.findByRole("dialog");

    await user.click(
      await screen.findByRole("checkbox", { name: /lockout procedure/i }),
    );
    await user.click(screen.getByRole("button", { name: /^materialize$/i }));

    await waitFor(() => {
      expect(requestSpy).toHaveBeenCalledWith({
        method: "POST",
        path: "/api/v1/risk-assessments/ra-1/materialize-controls",
        body: { control_ids: ["ctrl-1"], allow_under_review: false },
      });
    });
  });

  it("sends control_ids: null when nothing is checked (materialize all)", async () => {
    const user = userEvent.setup();
    const requestSpy = mockApiClient();

    renderDialog({ assessmentStatus: "approved" });
    await screen.findByRole("dialog");

    await user.click(screen.getByRole("button", { name: /^materialize$/i }));

    await waitFor(() => {
      expect(requestSpy).toHaveBeenCalledWith({
        method: "POST",
        path: "/api/v1/risk-assessments/ra-1/materialize-controls",
        body: { control_ids: null, allow_under_review: false },
      });
    });
  });

  it("never issues a request that writes to the assessment object itself", async () => {
    const user = userEvent.setup();
    const requestSpy = mockApiClient();

    renderDialog({ assessmentStatus: "approved" });
    await screen.findByRole("dialog");
    await user.click(screen.getByRole("button", { name: /^materialize$/i }));

    await waitFor(() => expect(requestSpy).toHaveBeenCalled());

    for (const call of requestSpy.mock.calls) {
      const options = call[0] as ApiRequestOptions;
      expect(options.path).not.toBe("/api/v1/risk-assessments/ra-1");
      if (options.path.startsWith("/api/v1/risk-assessments/ra-1")) {
        expect(["GET", "POST"]).toContain(options.method);
        expect(options.path).toContain("/materialize-controls");
      }
    }
  });
});

describe("MaterializeControlsDialog conflict routing", () => {
  it("opens the duplicate_materialization variant, never version_conflict, on a risk_control_already_materialized 409", async () => {
    const user = userEvent.setup();
    mockApiClient({
      materialize: () => {
        throw new ConflictError({
          message: "Already materialized",
          status: 409,
          code: "risk_control_already_materialized",
        });
      },
    });

    renderDialog({ assessmentStatus: "approved" });
    await screen.findByRole("dialog");
    await user.click(screen.getByRole("button", { name: /^materialize$/i }));

    expect(
      await screen.findByText("Controls already materialized"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Risk control changed elsewhere"),
    ).not.toBeInTheDocument();
  });
});

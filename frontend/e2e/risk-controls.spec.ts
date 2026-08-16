import { expect, test, type Page } from "@playwright/test";

const orgId = "22222222-2222-2222-2222-222222222222";
const orgIdB = "33333333-3333-3333-3333-333333333333";
const userId = "11111111-1111-1111-1111-111111111111";

const riskControlId = "dddddddd-dddd-dddd-dddd-dddddddddddd";
const hazardId = "cccccccc-cccc-cccc-cccc-cccccccccccc";
const riskAssessmentId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const proposedControlId = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee";
const replacementControlId = "ffffffff-ffff-ffff-ffff-ffffffffffff";
const otherControlId = "99999999-9999-9999-9999-999999999999";

/** Every `risk_control:*` permission the backend defines. */
const ALL_RC_PERMISSIONS = [
  "risk_control:read",
  "risk_control:create",
  "risk_control:update",
  "risk_control:assign",
  "risk_control:implement",
  "risk_control:verify",
  "risk_control:review",
  "risk_control:suspend",
  "risk_control:supersede",
  "risk_control:archive",
  "risk_control:cancel",
  "risk_control:materialize",
];

/** Full capability set for the main workflow, plus the read permissions the
 * object page needs to render hazard/assessment/activity context. */
const ALL_PERMISSIONS = [
  ...ALL_RC_PERMISSIONS,
  "hazard:read",
  "risk:read",
  "audit:read",
];

/** Read-only — proves no mutation affordance renders. */
const READER = ["risk_control:read"];

/** Mirrors the backend's `member` role grant (see
 * `backend/core/domain/value_objects/role_permissions.py`): read/create/
 * update/assign/implement/review/materialize — notably no verify, suspend,
 * supersede, archive, or cancel. */
const IMPLEMENTER = [
  "risk_control:read",
  "risk_control:create",
  "risk_control:update",
  "risk_control:assign",
  "risk_control:implement",
  "risk_control:review",
  "risk_control:materialize",
];

const VERIFIER = ["risk_control:read", "risk_control:verify"];
const REVIEWER = ["risk_control:read", "risk_control:review"];

async function mockAuth(
  page: Page,
  permissions: string[],
  options: {
    organizationId?: string;
    organizationName?: string;
    email?: string;
    displayName?: string;
  } = {},
) {
  const organizationId = options.organizationId ?? orgId;
  const organizationName = options.organizationName ?? "Acme Safety";
  const email = options.email ?? "user@example.com";
  const displayName = options.displayName ?? "Test User";

  await page.unroute("**/api/v1/auth/login").catch(() => undefined);
  await page.unroute("**/api/v1/auth/session").catch(() => undefined);
  await page.unroute("**/api/v1/auth/logout").catch(() => undefined);

  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "access-token",
        refresh_token: "refresh-token",
        token_type: "bearer",
        expires_in: 3600,
      }),
    });
  });
  await page.route("**/api/v1/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          id: userId,
          email,
          display_name: displayName,
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: organizationId,
            organization_name: organizationName,
            role: "member",
            status: "ACTIVE",
            permissions,
          },
        ],
      }),
    });
  });
  await page.route("**/api/v1/auth/logout", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
}

async function login(
  page: Page,
  email = "user@example.com",
  password = "secret-password",
) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
}

async function logout(page: Page, displayName = "Test User") {
  await page.getByRole("button", { name: new RegExp(displayName, "i") }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login/);
}

/** Toasts never auto-dismiss (see `Toast.tsx`) — clear them between steps
 * so a lingering success toast never intercepts the next click. */
async function dismissToasts(page: Page) {
  const dismissButtons = page.getByRole("button", {
    name: "Dismiss notification",
  });
  let count = await dismissButtons.count();
  while (count > 0) {
    await dismissButtons.first().click();
    count = await dismissButtons.count();
  }
}

function sampleRiskControl(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    id: riskControlId,
    organization_id: orgId,
    code: "RC-E2E",
    title: "E2E Risk Control",
    description: "Guard rail installed on the conveyor line",
    hierarchy_level: "engineering",
    control_nature: "preventive",
    source: {
      source_type: "risk_assessment",
      source_reference: null,
      risk_assessment_id: null,
      source_control_reference: null,
      assessment_version: null,
      assessment_approved_at: null,
      residual_level: null,
      snapshot: null,
    },
    hazard_id: null,
    risk_assessment_id: null,
    scope: [],
    owner: null,
    implementation: {
      target_start_date: null,
      target_completion_date: null,
      actual_start_date: null,
      actual_completion_date: null,
      implementation_method: "",
      milestones: [],
      dependencies: [],
      resource_notes: "",
      evidence_requirements: [],
      progress: 0,
      summary: "",
      evidence_waiver_reason: null,
    },
    evidence: [],
    verifications: [],
    review_schedule: {
      review_required: true,
      review_frequency_days: null,
      next_review_date: null,
      last_review_date: null,
      review_basis: "fixed_interval",
      escalation_policy_ref: null,
      no_review_reason: null,
    },
    competency_requirements: [],
    related_entities: [],
    extension_data: {},
    lifecycle_status: "draft",
    latest_effectiveness_result: null,
    next_review_date: null,
    is_overdue: false,
    verification_method_requirement: "",
    version: 1,
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-08-01T00:00:00Z",
    ...overrides,
  };
}

function conflictBody() {
  return JSON.stringify({
    error: {
      code: "risk_control_version_conflict",
      message: "Version conflict",
    },
  });
}

function notFoundBody() {
  return JSON.stringify({
    error: {
      code: "risk_control_not_found",
      message: "Risk control not found",
    },
  });
}

/**
 * Single stateful handler for `**​/api/v1/risk-controls**`, mirroring
 * `mockRiskAssessmentRoutes` in `risk-assessments.spec.ts`. Dispatches by
 * method + path suffix across all 14 lifecycle commands. Every command
 * checks `expected_version` against `current.version` and returns the
 * canonical 409 envelope on mismatch, else applies the change and
 * increments `version`.
 *
 * The GET list handler special-cases `limit=100&include_terminal=true` —
 * `MaterializeControlsDialog`'s own "already materialized" probe — and
 * always answers it with an empty list, so materialize scenarios never
 * need this helper to track cross-endpoint state.
 */
async function mockRiskControlRoutes(
  page: Page,
  initial: Record<string, unknown>,
) {
  const current: Record<string, unknown> = JSON.parse(JSON.stringify(initial));
  const controlId = initial.id as string;
  let nowCounter = 0;
  const now = () => {
    nowCounter += 1;
    return `2026-08-${String(10 + nowCounter).padStart(2, "0")}T00:00:00Z`;
  };
  let statusBeforeSuspend: string | null = null;

  await page.route("**/api/v1/risk-controls**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/risk-controls")) {
      const limit = url.searchParams.get("limit");
      const includeTerminal = url.searchParams.get("include_terminal");
      if (limit === "100" && includeTerminal === "true") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            items: [],
            pagination: { total: 0, offset: 0, limit: 100 },
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [current],
          pagination: { total: 1, offset: 0, limit: 25 },
        }),
      });
      return;
    }

    if (method === "GET" && url.pathname.endsWith(`/risk-controls/${controlId}`)) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (method === "GET" && /\/risk-controls\/[^/]+$/.test(url.pathname)) {
      // A different control id than the one this handler owns — 404.
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: notFoundBody(),
      });
      return;
    }

    if (method === "POST" && current) {
      const body = (request.postDataJSON() ?? {}) as Record<string, unknown>;
      const suffix = url.pathname.split("/").pop();
      const expectedVersion = body.expected_version;
      if (
        typeof expectedVersion === "number" &&
        expectedVersion !== (current.version as number)
      ) {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: conflictBody(),
        });
        return;
      }

      const bump = () => (current!.version = (current!.version as number) + 1);
      const implementation = current.implementation as Record<
        string,
        unknown
      >;
      const reviewSchedule = current.review_schedule as Record<
        string,
        unknown
      >;

      switch (suffix) {
        case "assign-owner": {
          const owner = body.owner as Record<string, unknown>;
          current.owner = {
            owner_type: owner.owner_type,
            owner_reference: owner.owner_reference,
            display_name_snapshot: owner.display_name_snapshot,
            assigned_at: now(),
            assigned_by: userId,
          };
          bump();
          break;
        }
        case "plan": {
          const impl = body.implementation as Record<string, unknown>;
          current.implementation = { ...implementation, ...impl };
          current.verification_method_requirement =
            body.verification_method_requirement ??
            current.verification_method_requirement;
          current.lifecycle_status = "planned";
          bump();
          break;
        }
        case "start-implementation": {
          current.lifecycle_status = "in_implementation";
          current.implementation = {
            ...implementation,
            actual_start_date: now(),
          };
          bump();
          break;
        }
        case "progress": {
          current.implementation = {
            ...implementation,
            progress: body.progress,
            summary: body.summary ?? implementation.summary,
          };
          bump();
          break;
        }
        case "evidence": {
          const evidence = current.evidence as unknown[];
          current.evidence = [
            ...evidence,
            {
              id: `evidence-${evidence.length + 1}`,
              evidence_type: body.evidence_type,
              external_reference: body.external_reference,
              title: body.title,
              description: body.description ?? "",
              captured_at: now(),
              captured_by: { value: userId },
              checksum: body.checksum ?? null,
              metadata: {},
            },
          ];
          bump();
          break;
        }
        case "complete-implementation": {
          current.lifecycle_status = "implemented";
          current.implementation = {
            ...implementation,
            progress: 100,
            actual_completion_date: now(),
            summary: body.summary,
            evidence_waiver_reason: body.evidence_waiver_reason ?? null,
          };
          bump();
          break;
        }
        case "verifications": {
          const verifications = current.verifications as unknown[];
          current.verifications = [
            ...verifications,
            {
              id: `verification-${verifications.length + 1}`,
              verification_type: body.verification_type ?? "initial",
              method: body.method,
              criteria: body.criteria ?? "",
              performed_at: now(),
              performed_by: { value: userId },
              result: body.result,
              rating: body.rating ?? null,
              findings: body.findings ?? "",
              evidence_refs: body.evidence_refs ?? [],
              next_action: body.next_action ?? null,
              next_review_date: body.next_review_date ?? null,
              profile_key: body.profile_key ?? "default",
              profile_version: body.profile_version ?? "1",
            },
          ];
          current.latest_effectiveness_result = body.result;
          if (body.result === "effective") {
            current.lifecycle_status = "verified_effective";
          } else if (body.result === "ineffective") {
            current.lifecycle_status = "verified_ineffective";
          }
          // partially_effective intentionally leaves lifecycle_status unchanged.
          if (body.next_review_date) {
            current.next_review_date = body.next_review_date;
          }
          bump();
          break;
        }
        case "schedule-review": {
          const schedule = body.schedule as Record<string, unknown>;
          current.review_schedule = { ...reviewSchedule, ...schedule };
          current.next_review_date =
            schedule.next_review_date ?? current.next_review_date;
          bump();
          break;
        }
        case "complete-review": {
          current.review_schedule = {
            ...reviewSchedule,
            last_review_date: now(),
            next_review_date:
              body.next_review_date ?? reviewSchedule.next_review_date,
          };
          current.next_review_date = current.review_schedule
            ? (current.review_schedule as Record<string, unknown>)
                .next_review_date
            : current.next_review_date;
          bump();
          if (body.verification) {
            const verification = body.verification as Record<
              string,
              unknown
            >;
            const verifications = current.verifications as unknown[];
            current.verifications = [
              ...verifications,
              {
                id: `verification-${verifications.length + 1}`,
                verification_type: verification.verification_type ?? "initial",
                method: verification.method,
                criteria: verification.criteria ?? "",
                performed_at: now(),
                performed_by: { value: userId },
                result: verification.result,
                rating: verification.rating ?? null,
                findings: verification.findings ?? "",
                evidence_refs: verification.evidence_refs ?? [],
                next_action: verification.next_action ?? null,
                next_review_date: verification.next_review_date ?? null,
                profile_key: verification.profile_key ?? "default",
                profile_version: verification.profile_version ?? "1",
              },
            ];
            current.latest_effectiveness_result = verification.result;
            if (verification.result === "effective") {
              current.lifecycle_status = "verified_effective";
            } else if (verification.result === "ineffective") {
              current.lifecycle_status = "verified_ineffective";
            }
            bump();
          }
          break;
        }
        case "suspend": {
          statusBeforeSuspend = current.lifecycle_status as string;
          current.lifecycle_status = "suspended";
          bump();
          break;
        }
        case "resume": {
          current.lifecycle_status = statusBeforeSuspend ?? "in_implementation";
          bump();
          break;
        }
        case "supersede": {
          current.lifecycle_status = "superseded";
          bump();
          break;
        }
        case "cancel": {
          current.lifecycle_status = "cancelled";
          bump();
          break;
        }
        case "archive": {
          current.lifecycle_status = "archived";
          bump();
          break;
        }
        default: {
          await route.fallback();
          return;
        }
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    await route.fallback();
  });
}

async function mockAuditRoutes(
  page: Page,
  events: Record<string, unknown>[] = [],
) {
  await page.route("**/api/v1/admin/audit-events**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: events,
        pagination: { total: events.length, offset: 0, limit: 50 },
      }),
    });
  });
}

test.describe("Risk Control lifecycle — main workflow", () => {
  test("materialize, assign, implement, verify effective, schedule review", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);

    const sampleAssessment = {
      id: riskAssessmentId,
      organization_id: orgId,
      hazard_id: hazardId,
      code: "RA-E2E",
      title: "E2E Risk Assessment",
      assessment_profile: "simple_5x5",
      assessed_object: { object_type: "workplace", reference: "Line A" },
      assessor_id: userId,
      assessment_date: "2026-08-01T00:00:00Z",
      review_schedule: {
        review_due_date: null,
        review_frequency_days: null,
        review_reason: null,
        triggered_by: null,
      },
      inherent_risk: null,
      residual_risk: null,
      controls: [
        {
          id: proposedControlId,
          control_type: "engineering",
          description: "Install guard rail",
          responsible: null,
          implemented: false,
          effective: null,
        },
      ],
      acceptance: null,
      competency_requirements: [],
      extension_references: {},
      status: "approved",
      superseded_by_id: null,
      archived_at: null,
      archived_by: null,
      approved_at: "2026-08-02T00:00:00Z",
      approved_by: userId,
      created_at: "2026-08-01T00:00:00Z",
      updated_at: "2026-08-02T00:00:00Z",
      version: 2,
    };

    const materialized = sampleRiskControl({
      hazard_id: hazardId,
      risk_assessment_id: riskAssessmentId,
      source: {
        source_type: "risk_assessment",
        source_reference: null,
        risk_assessment_id: { value: riskAssessmentId },
        source_control_reference: proposedControlId,
        assessment_version: 2,
        assessment_approved_at: "2026-08-02T00:00:00Z",
        residual_level: null,
        snapshot: null,
      },
    });

    await page.route("**/api/v1/risk-assessments**", async (route) => {
      const request = route.request();
      const method = request.method();
      const url = new URL(request.url());

      if (
        method === "GET" &&
        url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
      ) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(sampleAssessment),
        });
        return;
      }

      if (
        method === "POST" &&
        url.pathname.endsWith("/materialize-controls")
      ) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [materialized] }),
        });
        return;
      }

      await route.fallback();
    });

    await page.route("**/api/v1/hazards/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: hazardId,
          code: "HZ-RA-E2E",
          title: "E2E Hazard",
          status: "active",
        }),
      });
    });

    await mockRiskControlRoutes(page, materialized);

    await login(page);
    await page.goto(`/safety/risk-assessments/${riskAssessmentId}`);
    await expect(
      page.getByRole("heading", { name: "E2E Risk Assessment" }),
    ).toBeVisible();

    await page.getByRole("tab", { name: "Related controls" }).click();
    await page.getByRole("button", { name: "Materialize controls" }).click();
    await page
      .getByRole("checkbox", { name: /Engineering — Install guard rail/ })
      .check();
    await page.getByRole("button", { name: "Materialize" }).click();
    await expect(
      page.getByText(/Materialized 1 risk control/),
    ).toBeVisible();

    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("heading", { name: "E2E Risk Control", level: 1 }),
    ).toBeVisible();

    // Assign owner
    await page.getByRole("button", { name: "Assign owner" }).click();
    await page.getByLabel("Owner reference").fill("jane.doe");
    await page.getByLabel("Display name").fill("Jane Doe");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Assign owner" })
      .click();
    await expect(page.getByText("Jane Doe").first()).toBeVisible();
    await dismissToasts(page);

    // Plan implementation
    await page.getByRole("tab", { name: "Implementation" }).click();
    await page
      .getByRole("button", { name: "Plan implementation" })
      .first()
      .click();
    await page.getByLabel("Target completion date").fill("2026-09-30");
    await page
      .getByLabel("Verification method requirement")
      .fill("Visual inspection");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Plan implementation" })
      .click();
    await expect(page.getByLabel("Status: Planned").first()).toBeVisible();
    await dismissToasts(page);

    // Start implementation
    await page
      .getByRole("button", { name: "Start implementation" })
      .first()
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Start implementation" })
      .click();
    await expect(
      page.getByLabel("Status: In Implementation").first(),
    ).toBeVisible();
    await dismissToasts(page);

    // Update progress
    await page.getByRole("button", { name: "Update progress" }).click();
    await page.getByLabel("Progress (%)").fill("50");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Update progress" })
      .click();
    await dismissToasts(page);

    // Add evidence
    await page.getByRole("tab", { name: "Evidence" }).click();
    await page.getByRole("button", { name: "Add evidence" }).click();
    await page
      .getByLabel("External reference")
      .fill("DOC-100");
    await page.getByLabel("Title").fill("Guard rail photo");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Add evidence" })
      .click();
    await expect(page.getByText("Guard rail photo")).toBeVisible();
    await dismissToasts(page);

    // Complete implementation
    await page.getByRole("tab", { name: "Implementation" }).click();
    await page
      .getByRole("button", { name: "Complete implementation" })
      .first()
      .click();
    await page
      .getByLabel("Completion summary")
      .fill("Guard rail installed and verified in place.");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Complete implementation" })
      .click();
    await expect(page.getByLabel("Status: Implemented").first()).toBeVisible();
    await dismissToasts(page);

    // Record effectiveness verification
    await page.getByRole("tab", { name: "Verification" }).click();
    await page.getByRole("button", { name: "Record verification" }).click();
    await page.getByLabel("Method").fill("Site inspection");
    await page.getByRole("radio", { name: "Verified Effective" }).check();
    await page.getByLabel("Next review date").fill("2027-02-01");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Record verification" })
      .click();
    await expect(
      page.getByText("Verified Effective", { exact: true }).first(),
    ).toBeVisible();
    await dismissToasts(page);

    // Schedule review
    await page.getByRole("tab", { name: "Overview" }).click();
    await page.getByRole("button", { name: "Schedule review" }).first().click();
    await page.getByLabel("Next review date").fill("2027-03-01");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Schedule review" })
      .click();

    // Final Object Page assertions
    await expect(
      page.getByLabel("Status: Verified Effective").first(),
    ).toBeVisible();
    await expect(
      page.getByText("Verified Effective", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("Jane Doe").first()).toBeVisible();
    await expect(page.getByText("Mar 1, 2027").first()).toBeVisible();

    await page.getByRole("tab", { name: "Evidence" }).click();
    await expect(page.getByText("Guard rail photo")).toBeVisible();

    await page.getByRole("tab", { name: "Verification" }).click();
    await expect(page.getByText("Site inspection")).toBeVisible();
  });
});

test.describe("Risk Control lifecycle — effectiveness results", () => {
  test("effective result renders its own label and hides the others", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({
      lifecycle_status: "implemented",
      owner: {
        owner_type: "user",
        owner_reference: "jane.doe",
        display_name_snapshot: "Jane Doe",
        assigned_at: "2026-08-05T00:00:00Z",
        assigned_by: userId,
      },
      review_schedule: {
        review_required: true,
        review_frequency_days: 90,
        next_review_date: null,
        last_review_date: null,
        review_basis: "fixed_interval",
        escalation_policy_ref: null,
        no_review_reason: null,
      },
      evidence: [
        {
          id: "evidence-1",
          evidence_type: "document",
          external_reference: "DOC-1",
          title: "Pre-existing evidence",
          description: "",
          captured_at: "2026-08-05T00:00:00Z",
          captured_by: { value: userId },
          checksum: null,
          metadata: {},
        },
      ],
    });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("tab", { name: "Verification" }).click();
    await page.getByRole("button", { name: "Record verification" }).click();
    await page.getByLabel("Method").fill("Site inspection");
    await page.getByRole("radio", { name: "Verified Effective" }).check();
    await page.getByLabel("Next review date").fill("2027-01-01");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Record verification" })
      .click();

    await expect(
      page.getByText("Verified Effective", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("Verified Partially Effective")).toHaveCount(
      0,
    );
    await expect(page.getByText("Verified Ineffective")).toHaveCount(0);
  });

  test("ineffective result renders its own label and hides the others", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({
      lifecycle_status: "implemented",
      evidence: [
        {
          id: "evidence-1",
          evidence_type: "document",
          external_reference: "DOC-1",
          title: "Pre-existing evidence",
          description: "",
          captured_at: "2026-08-05T00:00:00Z",
          captured_by: { value: userId },
          checksum: null,
          metadata: {},
        },
      ],
    });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("tab", { name: "Verification" }).click();
    await page.getByRole("button", { name: "Record verification" }).click();
    await page.getByLabel("Method").fill("Site inspection");
    await page.getByRole("radio", { name: "Verified Ineffective" }).check();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Record verification" })
      .click();

    await expect(
      page.getByText("Verified Ineffective", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("Verified Effective", { exact: true })).toHaveCount(
      0,
    );
    await expect(page.getByText("Verified Partially Effective")).toHaveCount(
      0,
    );
  });

  test("partially effective result never collapses into effective or ineffective, and leaves the status badge unchanged", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({
      lifecycle_status: "implemented",
      evidence: [
        {
          id: "evidence-1",
          evidence_type: "document",
          external_reference: "DOC-1",
          title: "Pre-existing evidence",
          description: "",
          captured_at: "2026-08-05T00:00:00Z",
          captured_by: { value: userId },
          checksum: null,
          metadata: {},
        },
      ],
    });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(page.getByLabel("Status: Implemented").first()).toBeVisible();

    await page.getByRole("tab", { name: "Verification" }).click();
    await page.getByRole("button", { name: "Record verification" }).click();
    await page.getByLabel("Method").fill("Site inspection");
    await page
      .getByRole("radio", { name: "Verified Partially Effective" })
      .check();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Record verification" })
      .click();

    await expect(
      page.getByText("Verified Partially Effective", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("Verified Effective", { exact: true })).toHaveCount(
      0,
    );
    await expect(
      page.getByText("Verified Ineffective", { exact: true }),
    ).toHaveCount(0);

    // Lifecycle status badge is unchanged — still "Implemented".
    await expect(page.getByLabel("Status: Implemented").first()).toBeVisible();
  });
});

test.describe("Risk Control lifecycle — negative scenarios", () => {
  test("read-only user cannot mutate the control", async ({ page }) => {
    await mockAuth(page, READER);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({
      lifecycle_status: "draft",
      owner: {
        owner_type: "user",
        owner_reference: "jane.doe",
        display_name_snapshot: "Jane Doe",
        assigned_at: "2026-08-05T00:00:00Z",
        assigned_by: userId,
      },
    });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("heading", { name: "E2E Risk Control", level: 1 }),
    ).toBeVisible();

    await expect(
      page.getByRole("button", { name: "Assign owner" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Plan implementation" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Verify effectiveness" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Archive control" }),
    ).toHaveCount(0);
  });

  test("no verify permission hides the Verify action", async ({ page }) => {
    await mockAuth(page, IMPLEMENTER);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "implemented" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("heading", { name: "E2E Risk Control", level: 1 }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Verify effectiveness" }),
    ).toHaveCount(0);
  });

  test("verify-only user sees Verify but not implement/review actions", async ({
    page,
  }) => {
    await mockAuth(page, VERIFIER);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "implemented" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("button", { name: "Verify effectiveness" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Schedule review" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Plan implementation" }),
    ).toHaveCount(0);
  });

  test("review-only user sees Schedule review but not Verify", async ({
    page,
  }) => {
    await mockAuth(page, REVIEWER);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "implemented" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("button", { name: "Schedule review" }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Verify effectiveness" }),
    ).toHaveCount(0);
  });

  test("unknown control shows not found", async ({ page }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl();
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${otherControlId}`);
    await expect(page.getByText("Risk control not found")).toBeVisible();
  });

  test("cross-tenant control shows the identical not-found copy", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl();
    await mockRiskControlRoutes(page, control);

    await login(page);
    // A control id belonging to another organization — the backend answers
    // with 404, indistinguishable from a genuinely unknown id.
    await page.goto(`/safety/risk-controls/${otherControlId}`);
    await expect(page.getByText("Risk control not found")).toBeVisible();
    await expect(page.getByText(/denied/i)).toHaveCount(0);
    await expect(page.getByText(/forbidden/i)).toHaveCount(0);
  });

  test("stale mutation shows the conflict dialog and does not auto-retry", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({
      lifecycle_status: "suspended",
      version: 3,
    });

    let resumeAttempts = 0;
    await page.route("**/api/v1/risk-controls**", async (route) => {
      const request = route.request();
      const method = request.method();
      const url = new URL(request.url());

      if (method === "GET" && url.pathname.endsWith(`/risk-controls/${riskControlId}`)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(control),
        });
        return;
      }

      if (method === "POST" && url.pathname.endsWith("/resume")) {
        resumeAttempts += 1;
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: conflictBody(),
        });
        return;
      }

      await route.fallback();
    });

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("button", { name: "Resume control" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Resume control" })
      .click();

    await expect(
      page.getByRole("heading", { name: "Risk control changed elsewhere" }),
    ).toBeVisible();
    expect(resumeAttempts).toBe(1);
  });

  test("duplicate materialization shows the duplicate-variant dialog", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);

    const sampleAssessment = {
      id: riskAssessmentId,
      organization_id: orgId,
      hazard_id: hazardId,
      code: "RA-E2E",
      title: "E2E Risk Assessment",
      assessment_profile: "simple_5x5",
      assessed_object: { object_type: "workplace", reference: "Line A" },
      assessor_id: userId,
      assessment_date: "2026-08-01T00:00:00Z",
      review_schedule: {
        review_due_date: null,
        review_frequency_days: null,
        review_reason: null,
        triggered_by: null,
      },
      inherent_risk: null,
      residual_risk: null,
      controls: [
        {
          id: proposedControlId,
          control_type: "engineering",
          description: "Install guard rail",
          responsible: null,
          implemented: false,
          effective: null,
        },
      ],
      acceptance: null,
      competency_requirements: [],
      extension_references: {},
      status: "approved",
      superseded_by_id: null,
      archived_at: null,
      archived_by: null,
      approved_at: "2026-08-02T00:00:00Z",
      approved_by: userId,
      created_at: "2026-08-01T00:00:00Z",
      updated_at: "2026-08-02T00:00:00Z",
      version: 2,
    };

    await page.route("**/api/v1/risk-assessments**", async (route) => {
      const request = route.request();
      const method = request.method();
      const url = new URL(request.url());

      if (
        method === "GET" &&
        url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
      ) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(sampleAssessment),
        });
        return;
      }

      if (
        method === "POST" &&
        url.pathname.endsWith("/materialize-controls")
      ) {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "risk_control_already_materialized",
              message: "One or more controls are already materialized.",
            },
          }),
        });
        return;
      }

      await route.fallback();
    });

    await page.route("**/api/v1/risk-controls**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          pagination: { total: 0, offset: 0, limit: 100 },
        }),
      });
    });

    await login(page);
    await page.goto(`/safety/risk-assessments/${riskAssessmentId}`);
    await page.getByRole("tab", { name: "Related controls" }).click();
    await page.getByRole("button", { name: "Materialize controls" }).click();
    await page
      .getByRole("checkbox", { name: /Engineering — Install guard rail/ })
      .check();
    await page.getByRole("button", { name: "Materialize" }).click();

    await expect(
      page.getByRole("heading", { name: "Controls already materialized" }),
    ).toBeVisible();
  });

  test("invalid lifecycle transition is rejected and leaves the status badge unchanged", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "planned" });

    await page.route("**/api/v1/risk-controls**", async (route) => {
      const request = route.request();
      const method = request.method();
      const url = new URL(request.url());

      if (method === "GET" && url.pathname.endsWith(`/risk-controls/${riskControlId}`)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(control),
        });
        return;
      }

      if (method === "POST" && url.pathname.endsWith("/start-implementation")) {
        await route.fulfill({
          status: 422,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "invalid_risk_control_transition",
              message: "Cannot start implementation from status planned.",
            },
          }),
        });
        return;
      }

      await route.fallback();
    });

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("tab", { name: "Implementation" }).click();
    await page.getByRole("button", { name: "Start implementation" }).first().click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Start implementation" })
      .click();

    await expect(
      page.getByText("Cannot start implementation from status planned."),
    ).toBeVisible();
    await expect(page.getByLabel("Status: Planned").first()).toBeVisible();
  });

  test("logout clears data — re-login as a different org shows no stale rows", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS, {
      organizationId: orgId,
      organizationName: "Acme Safety",
    });
    await mockAuditRoutes(page);
    const controlA = sampleRiskControl({ code: "RC-ORG-A" });
    await mockRiskControlRoutes(page, controlA);

    await login(page);
    await page.goto("/safety/risk-controls");
    await expect(page.getByText("RC-ORG-A")).toBeVisible();

    await logout(page);

    await mockAuth(page, ["risk_control:read"], {
      organizationId: orgIdB,
      organizationName: "Other Org",
      email: "user2@example.com",
      displayName: "Second User",
    });
    await page.unroute("**/api/v1/risk-controls**").catch(() => undefined);
    await page.route("**/api/v1/risk-controls**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          pagination: { total: 0, offset: 0, limit: 25 },
        }),
      });
    });

    await login(page, "user2@example.com");
    await page.goto("/safety/risk-controls");
    await expect(page.getByText("RC-ORG-A")).toHaveCount(0);
    await expect(page.getByText("No risk controls yet")).toBeVisible();
  });

  test("no delete affordance exists on any reachable status", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    await login(page);
    const statuses = [
      "draft",
      "planned",
      "in_implementation",
      "implemented",
      "verified_effective",
      "verified_ineffective",
      "suspended",
      "superseded",
      "archived",
      "cancelled",
    ];

    for (const status of statuses) {
      const control = sampleRiskControl({ lifecycle_status: status });
      await page.unroute("**/api/v1/risk-controls**").catch(() => undefined);
      await mockRiskControlRoutes(page, control);
      await page.goto(`/safety/risk-controls/${riskControlId}`);
      await expect(
        page.getByRole("heading", { name: "E2E Risk Control", level: 1 }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: /delete/i }),
      ).toHaveCount(0);
    }
  });
});

test.describe("Risk Control lifecycle — terminal commands", () => {
  test("suspend then resume returns to the prior status", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "in_implementation" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);

    await page.getByRole("button", { name: "Suspend control" }).click();
    await page.getByLabel("Reason").fill("Waiting on parts");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Suspend control" })
      .click();
    await expect(page.getByLabel("Status: Suspended").first()).toBeVisible();

    await page.getByRole("button", { name: "Resume control" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Resume control" })
      .click();
    await expect(
      page.getByLabel("Status: In Implementation").first(),
    ).toBeVisible();
  });

  test("archive leaves the control readable by direct link", async ({
    page,
  }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "implemented" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("button", { name: "Archive control" }).click();
    await page.getByLabel("Reason").fill("Control retired");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Archive control" })
      .click();
    await expect(page.getByLabel("Status: Archived").first()).toBeVisible();

    // Archiving is not deletion — the control stays readable by direct link.
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await expect(
      page.getByRole("heading", { name: "E2E Risk Control", level: 1 }),
    ).toBeVisible();
    await expect(page.getByLabel("Status: Archived").first()).toBeVisible();
    await expect(page.getByText("Risk control not found")).toHaveCount(0);
  });

  test("cancel moves the control to cancelled", async ({ page }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "planned" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("button", { name: "Cancel control" }).click();
    await page
      .getByLabel("Reason")
      .fill("Assessment superseded before implementation");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Cancel control" })
      .click();
    await expect(page.getByLabel("Status: Cancelled").first()).toBeVisible();
  });

  test("supersede moves the control to superseded", async ({ page }) => {
    await mockAuth(page, ALL_PERMISSIONS);
    await mockAuditRoutes(page);
    const control = sampleRiskControl({ lifecycle_status: "implemented" });
    await mockRiskControlRoutes(page, control);

    await login(page);
    await page.goto(`/safety/risk-controls/${riskControlId}`);
    await page.getByRole("button", { name: "Supersede control" }).click();
    await page
      .getByLabel("Replacement control ID")
      .fill(replacementControlId);
    await page
      .getByLabel("Reason")
      .fill("Replaced by an improved guard design");
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Supersede control" })
      .click();
    await expect(page.getByLabel("Status: Superseded").first()).toBeVisible();
  });
});

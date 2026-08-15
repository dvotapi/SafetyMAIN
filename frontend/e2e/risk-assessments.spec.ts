import { expect, test, type Page } from "@playwright/test";

const riskAssessmentId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const hazardId = "cccccccc-cccc-cccc-cccc-cccccccccccc";
const orgId = "22222222-2222-2222-2222-222222222222";

const allPerms = [
  "risk:read",
  "risk:create",
  "risk:update",
  "risk:approve",
  "risk:archive",
  "risk_control:read",
  "audit:read",
  "hazard:read",
];

async function mockAuth(page: Page, permissions: string[]) {
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
          id: "11111111-1111-1111-1111-111111111111",
          email: "user@example.com",
          display_name: "Test User",
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: orgId,
            organization_name: "Acme Safety",
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

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill("user@example.com");
  await page.getByLabel("Password").fill("secret-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
}

function sampleHazard(overrides: Record<string, unknown> = {}) {
  return {
    id: hazardId,
    organization_id: orgId,
    code: "HZ-RA-E2E",
    title: "E2E Hazard for RA",
    description: "Active hazard for risk assessment e2e",
    category: "physical",
    safety_directions: ["occupational_safety"],
    source: "inspection",
    affected_subjects: ["employee"],
    location_reference: "Line 1",
    process_reference: null,
    equipment_reference: null,
    extension_references: {},
    status: "active",
    identified_at: "2026-07-25T00:00:00Z",
    identified_by: "11111111-1111-1111-1111-111111111111",
    reviewed_at: null,
    reviewed_by: null,
    archived_at: null,
    archived_by: null,
    created_at: "2026-07-25T00:00:00Z",
    updated_at: "2026-07-25T00:00:00Z",
    version: 1,
    ...overrides,
  };
}

function inherentRiskFromPatch(
  body: Record<string, unknown>,
): Record<string, unknown> | null {
  const inherent = body.inherent_risk as
    | {
        probability?: number;
        severity?: number;
        factors?: Array<{ factor: string; score: number }>;
        explanation?: string;
      }
    | undefined;
  if (!inherent) {
    return null;
  }
  const factors = (inherent.factors ??
    [
      inherent.probability != null
        ? { factor: "probability", score: inherent.probability }
        : null,
      inherent.severity != null
        ? { factor: "severity", score: inherent.severity }
        : null,
    ].filter(Boolean)) as Array<{ factor: string; score: number }>;
  if (factors.length === 0) {
    return null;
  }
  const prob =
    inherent.probability ??
    factors.find((item) => item.factor === "probability")?.score ??
    1;
  const sev =
    inherent.severity ??
    factors.find((item) => item.factor === "severity")?.score ??
    1;
  const score = prob * sev;
  const level =
    score >= 20
      ? "extreme"
      : score >= 12
        ? "high"
        : score >= 6
          ? "medium"
          : "low";
  return {
    factors,
    level,
    explanation: inherent.explanation ?? "",
  };
}

function sampleRiskAssessment(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    id: riskAssessmentId,
    organization_id: orgId,
    hazard_id: hazardId,
    code: "RA-E2E",
    title: "E2E Risk Assessment",
    assessment_profile: "simple_5x5",
    assessed_object: { object_type: "workplace", reference: "Line A" },
    assessor_id: "11111111-1111-1111-1111-111111111111",
    assessment_date: "2026-08-01T00:00:00Z",
    review_schedule: {
      review_due_date: null,
      review_frequency_days: null,
      review_reason: null,
      triggered_by: null,
    },
    inherent_risk: null,
    residual_risk: null,
    controls: [],
    acceptance: null,
    competency_requirements: [],
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
    ...overrides,
  };
}

async function mockEmptyRelatedRoutes(page: Page) {
  await page.route("**/api/v1/risk-controls**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        pagination: { total: 0, offset: 0, limit: 50 },
      }),
    });
  });

  await page.route("**/api/v1/admin/audit-events**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        pagination: { total: 0, offset: 0, limit: 50 },
      }),
    });
  });
}

async function mockHazardRoutes(page: Page) {
  const hazard = sampleHazard();
  await page.route("**/api/v1/hazards**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/hazards")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [hazard],
          pagination: { total: 1, offset: 0, limit: 50 },
        }),
      });
      return;
    }

    if (method === "GET" && url.pathname.endsWith(`/hazards/${hazardId}`)) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(hazard),
      });
      return;
    }

    await route.fallback();
  });
}

async function fillCreateForm(page: Page) {
  await page.getByLabel("Hazard").click();
  await page
    .getByRole("option", { name: "HZ-RA-E2E — E2E Hazard for RA" })
    .click();
  await page.getByLabel("Code").fill("RA-E2E");
  await page.getByLabel("Title").fill("E2E Risk Assessment");
  await page.getByLabel("Assessed object reference").fill("Line A");
  await page.getByLabel("Probability (1–5)").first().click();
  await page.getByRole("option", { name: "3", exact: true }).click();
  await page.getByLabel("Severity (1–5)").first().click();
  await page.getByRole("option", { name: "4", exact: true }).click();
}

test("risk assessment create edit submit approve and archive flow", async ({
  page,
}) => {
  await mockAuth(page, allPerms);
  await mockEmptyRelatedRoutes(page);
  await mockHazardRoutes(page);

  let current = sampleRiskAssessment();
  const listItems: Record<string, unknown>[] = [];

  await page.route("**/api/v1/risk-assessments**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/risk-assessments")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: listItems,
          pagination: { total: listItems.length, offset: 0, limit: 50 },
        }),
      });
      return;
    }

    if (method === "POST" && url.pathname.endsWith("/risk-assessments")) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = sampleRiskAssessment({
        code: body.code,
        title: body.title,
        hazard_id: body.hazard_id,
        assessment_profile: body.assessment_profile,
        assessed_object: body.assessed_object,
        assessment_date: body.assessment_date ?? current.assessment_date,
        inherent_risk: null,
      });
      listItems.push(current);
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "GET" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "POST" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}/approve`)
    ) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = {
        ...current,
        status: "approved",
        version: Number(current.version ?? 1) + 1,
        approved_at: "2026-08-02T00:00:00Z",
        approved_by: "11111111-1111-1111-1111-111111111111",
        acceptance: body.acceptance ?? current.acceptance,
      };
      listItems[0] = current;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "POST" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}/archive`)
    ) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = {
        ...current,
        status: "archived",
        version: Number(current.version ?? 1) + 1,
        archived_at: "2026-08-03T00:00:00Z",
        archived_by: "11111111-1111-1111-1111-111111111111",
        archive_reason: body.reason,
      };
      listItems[0] = current;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "PATCH" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
    ) {
      const body = request.postDataJSON() as Record<string, unknown>;
      if (body.expected_version !== Number(current.version ?? 1)) {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "risk_assessment_version_conflict",
              message: "Version conflict",
            },
          }),
        });
        return;
      }

      const nextInherent =
        inherentRiskFromPatch(body) ?? current.inherent_risk ?? null;
      current = {
        ...current,
        title: (body.title as string) ?? current.title,
        inherent_risk: nextInherent,
        version: Number(current.version ?? 1) + 1,
        status: body.submit_for_review ? "under_review" : current.status,
        ...(body.submit_for_review
          ? {
              acceptance: {
                decision: "not_accepted",
                justification: "Escalate if residual risk remains",
                reviewer_id: null,
                approved_at: null,
              },
            }
          : {}),
      };
      listItems[0] = current;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    await route.fallback();
  });

  await login(page);
  await page.goto("/safety/risk-assessments/new");
  await expect(
    page.getByRole("heading", { name: "Create risk assessment" }),
  ).toBeVisible();
  await fillCreateForm(page);
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page).toHaveURL(`/safety/risk-assessments/${riskAssessmentId}`);
  await expect(
    page.getByRole("heading", { name: "E2E Risk Assessment" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Edit draft" }).click();
  await page.getByLabel("Title").fill("E2E Risk Assessment Updated");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("heading", { name: "E2E Risk Assessment Updated" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Submit for review" }).click();
  await page.getByRole("button", { name: "Submit for review" }).last().click();
  await expect(page.getByLabel("Status: Under Review").first()).toBeVisible();

  await page.getByRole("button", { name: "Approve assessment" }).click();
  const approveDialog = page.getByRole("dialog", {
    name: "Approve assessment",
  });
  await expect(approveDialog.getByText("Not Accepted")).toBeVisible();
  await approveDialog
    .getByRole("button", { name: "Approve assessment" })
    .click();
  await expect(page.getByLabel("Status: Approved").first()).toBeVisible();

  await page.getByRole("button", { name: "Archive assessment" }).click();
  const archiveDialog = page.getByRole("dialog", {
    name: "Archive assessment",
  });
  await archiveDialog.getByRole("textbox").fill("No longer applicable.");
  await archiveDialog
    .getByRole("button", { name: "Archive assessment" })
    .click();
  await expect(page.getByLabel("Status: Archived").first()).toBeVisible();
});

test("read-only user cannot create risk assessments", async ({ page }) => {
  await mockAuth(page, ["risk:read"]);
  await mockEmptyRelatedRoutes(page);

  await page.route("**/api/v1/risk-assessments**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        pagination: { total: 0, offset: 0, limit: 50 },
      }),
    });
  });

  await login(page);
  await page.goto("/safety/risk-assessments");
  await expect(
    page.getByRole("heading", { name: "Risk Assessments" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Create risk assessment" }),
  ).toHaveCount(0);
  await page.goto("/safety/risk-assessments/new");
  await expect(page.getByText("Cannot create risk assessments")).toBeVisible();
});

test("create validation error maps title field", async ({ page }) => {
  await mockAuth(page, allPerms);
  await mockEmptyRelatedRoutes(page);
  await mockHazardRoutes(page);

  await page.route("**/api/v1/risk-assessments**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/risk-assessments")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [],
          pagination: { total: 0, offset: 0, limit: 50 },
        }),
      });
      return;
    }

    if (method === "POST" && url.pathname.endsWith("/risk-assessments")) {
      await route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "validation_error",
            message: "Validation failed",
            details: {
              title: "Title must be at least 3 characters",
            },
          },
        }),
      });
      return;
    }

    await route.fallback();
  });

  await login(page);
  await page.goto("/safety/risk-assessments/new");
  await fillCreateForm(page);
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Title must be at least 3 characters" })
      .first(),
  ).toBeVisible();
});

test("stale edit shows conflict dialog", async ({ page }) => {
  await mockAuth(page, [
    "risk:read",
    "risk:update",
    "risk:approve",
    "risk:archive",
    "risk_control:read",
    "audit:read",
    "hazard:read",
  ]);
  await mockEmptyRelatedRoutes(page);
  await mockHazardRoutes(page);

  const current = sampleRiskAssessment({
    version: 2,
    inherent_risk: {
      factors: [
        { factor: "probability", score: 3 },
        { factor: "severity", score: 4 },
      ],
      level: "high",
      explanation: "",
    },
  });

  await page.route(
    `**/api/v1/risk-assessments/${riskAssessmentId}`,
    async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(current),
        });
        return;
      }
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "risk_assessment_version_conflict",
              message: "Version conflict",
            },
          }),
        });
        return;
      }
      await route.fallback();
    },
  );

  await login(page);
  await page.goto(`/safety/risk-assessments/${riskAssessmentId}`);
  await page.getByRole("button", { name: "Edit draft" }).click();
  await page.getByLabel("Title").fill("Conflict title");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("heading", { name: "Risk assessment changed elsewhere" }),
  ).toBeVisible();
});

test("unknown risk assessment shows not found", async ({ page }) => {
  await mockAuth(page, ["risk:read"]);
  await mockEmptyRelatedRoutes(page);

  await page.route(
    `**/api/v1/risk-assessments/${riskAssessmentId}`,
    async (route) => {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "risk_assessment_not_found",
            message: "Not found",
          },
        }),
      });
    },
  );

  await login(page);
  await page.goto(`/safety/risk-assessments/${riskAssessmentId}`);
  await expect(page.getByText("Risk assessment not found")).toBeVisible();
});

test("partial create recovery retries risk detail patch", async ({ page }) => {
  await mockAuth(page, allPerms);
  await mockEmptyRelatedRoutes(page);
  await mockHazardRoutes(page);

  let current = sampleRiskAssessment();
  let patchAttempts = 0;

  await page.route("**/api/v1/risk-assessments**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/risk-assessments")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [current],
          pagination: { total: 1, offset: 0, limit: 50 },
        }),
      });
      return;
    }

    if (method === "POST" && url.pathname.endsWith("/risk-assessments")) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = sampleRiskAssessment({
        code: body.code,
        title: body.title,
        hazard_id: body.hazard_id,
        assessment_profile: body.assessment_profile,
        assessed_object: body.assessed_object,
        inherent_risk: null,
      });
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "GET" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (
      method === "PATCH" &&
      url.pathname.endsWith(`/risk-assessments/${riskAssessmentId}`)
    ) {
      patchAttempts += 1;
      if (patchAttempts === 1) {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "internal_error",
              message: "Patch failed",
            },
          }),
        });
        return;
      }

      const body = request.postDataJSON() as Record<string, unknown>;
      current = {
        ...current,
        inherent_risk: inherentRiskFromPatch(body),
        version: Number(current.version ?? 1) + 1,
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    await route.fallback();
  });

  await login(page);
  await page.goto("/safety/risk-assessments/new");
  await fillCreateForm(page);
  await page.getByRole("button", { name: "Create draft" }).click();

  await expect(
    page.getByRole("alert").filter({
      hasText: "Draft created with incomplete details",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Retry saving risk details" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Retry saving risk details" }).click();
  await expect(page).toHaveURL(`/safety/risk-assessments/${riskAssessmentId}`);
  await expect(
    page.getByRole("heading", { name: "E2E Risk Assessment" }),
  ).toBeVisible();
});

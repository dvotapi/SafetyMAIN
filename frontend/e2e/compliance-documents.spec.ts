import { expect, test, type Page } from "@playwright/test";

const DOCUMENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
const TYPE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb";
const USER_ID = "11111111-1111-1111-1111-111111111111";
const ORG_ID = "22222222-2222-2222-2222-222222222222";

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
          id: USER_ID,
          email: "user@example.com",
          display_name: "Test User",
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: ORG_ID,
            organization_name: "Acme Safety",
            role: "admin",
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

function sampleType() {
  return {
    id: TYPE_ID,
    organization_id: ORG_ID,
    code: "local_act",
    title_ru: "Локальный акт",
    safety_domain: "occupational",
    subject_kind: "organization",
    review_period_months: 36,
    validity_months: null,
    periodicity_months: null,
    warning_thresholds_days: [30],
    requires_acknowledgement: false,
    requires_approval_order: false,
    legal_basis: "ТК РФ",
    legal_basis_reference: null,
    is_active: true,
    created_at: "2026-10-01T00:00:00Z",
    updated_at: "2026-10-01T00:00:00Z",
  };
}

function sampleDocument(overrides: Record<string, unknown> = {}) {
  return {
    id: DOCUMENT_ID,
    organization_id: ORG_ID,
    document_type_id: TYPE_ID,
    subject_kind: "organization",
    subject_id: null,
    code: "CD-E2E",
    title: "Положение E2E",
    status: "draft",
    issued_at: null,
    effective_from: null,
    next_review_at: null,
    approved_by_document_id: null,
    supersedes_document_id: null,
    superseded_by_document_id: null,
    applicability: {
      positions: [],
      work_types: [],
      departments: [],
      asset_ids: [],
    },
    source: "manual",
    current_file: null,
    notes: "",
    status_before_archive: null,
    archive_reason: null,
    is_review_due: false,
    created_at: "2026-10-01T00:00:00Z",
    created_by: USER_ID,
    updated_at: "2026-10-01T00:00:00Z",
    updated_by: USER_ID,
    version: 1,
    ...overrides,
  };
}

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Электронная почта").fill("user@example.com");
  await page.getByLabel("Пароль").fill("secret-password");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
}

test("compliance document create → upload → approve → activate", async ({
  page,
}) => {
  await mockAuth(page, [
    "compliance_document:read",
    "compliance_document:create",
    "compliance_document:update",
    "compliance_document:approve",
    "compliance_document:activate",
    "compliance_document:archive",
  ]);

  let current = sampleDocument();
  const listItems: unknown[] = [];

  await page.route("**/api/v1/document-types**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [sampleType()] }),
    });
  });

  await page.route(
    "**/api/v1/compliance-documents/*/files/upload-url",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          upload_id: "upload-1",
          bucket: "bkt",
          key: `${ORG_ID}/compliance_document/${DOCUMENT_ID}/upload-1/file.pdf`,
          url: "https://signed.example/put",
          method: "PUT",
          headers: { "Content-Type": "application/pdf" },
          expires_at: "2030-01-01T00:00:00Z",
        }),
      });
    },
  );

  await page.route("https://signed.example/put", async (route) => {
    await route.fulfill({ status: 200, body: "" });
  });

  await page.route(
    "**/api/v1/compliance-documents/*/files/confirm",
    async (route) => {
      current = sampleDocument({
        ...current,
        version: current.version + 1,
        current_file: {
          id: "ffffffff-ffff-ffff-ffff-ffffffffffff",
          bucket: "bkt",
          key: `${ORG_ID}/compliance_document/${DOCUMENT_ID}/upload-1/file.pdf`,
          size_bytes: 4,
          content_type: "application/pdf",
          sha256: "a".repeat(64),
          original_filename: "briefing.pdf",
          uploaded_at: "2026-10-01T00:00:00Z",
          uploaded_by: USER_ID,
        },
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
    },
  );

  await page.route(
    "**/api/v1/compliance-documents/*/files/versions",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: current.current_file ? [current.current_file] : [],
        }),
      });
    },
  );

  await page.route(
    "**/api/v1/compliance-documents/*/approve",
    async (route) => {
      current = sampleDocument({
        ...current,
        status: "approved",
        version: current.version + 1,
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
    },
  );

  await page.route(
    "**/api/v1/compliance-documents/*/activate",
    async (route) => {
      current = sampleDocument({
        ...current,
        status: "active",
        version: current.version + 1,
        effective_from: "2026-10-01",
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
    },
  );

  await page.route("**/api/v1/compliance-documents**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "POST" && url.pathname.endsWith("/compliance-documents")) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = sampleDocument({
        code: body.code,
        title: body.title,
        effective_from: body.effective_from ?? null,
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
      url.pathname.endsWith(`/compliance-documents/${DOCUMENT_ID}`)
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (method === "GET" && url.pathname.endsWith("/compliance-documents")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: listItems,
          pagination: { total: listItems.length, offset: 0, limit: 25 },
        }),
      });
      return;
    }

    await route.fallback();
  });

  await login(page);
  await page.goto("/compliance-documents");
  await page.getByTestId("compliance-document-create-link").click();

  await page.waitForURL("**/compliance-documents/new");
  await expect(
    page.getByRole("heading", { name: /Создать документ соответствия/i }),
  ).toBeVisible();

  // Pick type via Select (shadcn style button).
  await page.locator("#cd-type").click();
  await page.getByRole("option", { name: /Локальный акт/i }).click();

  await page.locator("#cd-code").fill("CD-E2E");
  await page.locator("#cd-title").fill("Положение E2E");
  await page.locator("#cd-effective").fill("2026-10-01");

  await page.getByRole("button", { name: "Создать" }).click();

  await page.waitForURL(`**/compliance-documents/${DOCUMENT_ID}`);
  await expect(page.getByText("Черновик")).toBeVisible();

  // Upload file.
  await page.getByTestId("compliance-document-upload-trigger").click();
  const bytes = Buffer.from("test");
  await page.getByTestId("compliance-document-upload-input").setInputFiles({
    name: "briefing.pdf",
    mimeType: "application/pdf",
    buffer: bytes,
  });
  await page.getByRole("button", { name: "Загрузить" }).click();

  await expect(page.getByText("briefing.pdf")).toBeVisible({ timeout: 10_000 });

  // Approve → Activate.
  await page.getByRole("button", { name: "Утвердить" }).click();
  await expect(
    page.getByRole("button", { name: "Ввести в действие" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Ввести в действие" }).click();
  await expect(page.getByText("Документ введён в действие")).toBeVisible();
});

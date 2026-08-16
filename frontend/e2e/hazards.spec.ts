import { expect, test, type Page } from "@playwright/test";

const hazardId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";

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
            organization_id: "22222222-2222-2222-2222-222222222222",
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

function sampleHazard(overrides: Record<string, unknown> = {}) {
  return {
    id: hazardId,
    organization_id: "22222222-2222-2222-2222-222222222222",
    code: "HZ-E2E",
    title: "E2E Hazard",
    description: "Created in e2e",
    category: "physical",
    safety_directions: ["occupational_safety"],
    source: "inspection",
    affected_subjects: ["employee"],
    location_reference: "Line 1",
    process_reference: null,
    equipment_reference: null,
    extension_references: {},
    status: "draft",
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

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Электронная почта").fill("user@example.com");
  await page.getByLabel("Пароль").fill("secret-password");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
}

test("hazard create activate and registry flow", async ({ page }) => {
  const allPerms = [
    "hazard:read",
    "hazard:create",
    "hazard:update",
    "hazard:activate",
    "hazard:archive",
    "hazard:restore",
    "risk:read",
    "audit:read",
  ];
  await mockAuth(page, allPerms);

  let current = sampleHazard();
  const listItems: unknown[] = [];

  await page.route("**/api/v1/hazards**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());

    if (method === "GET" && url.pathname.endsWith("/hazards")) {
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

    if (method === "POST" && url.pathname.endsWith("/hazards")) {
      const body = request.postDataJSON() as Record<string, unknown>;
      current = sampleHazard({
        code: body.code,
        title: body.title,
        description: body.description ?? "",
        category: body.category,
        safety_directions: body.safety_directions,
        source: body.source,
      });
      listItems.push(current);
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (method === "GET" && url.pathname.endsWith(`/hazards/${hazardId}`)) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(current),
      });
      return;
    }

    if (method === "PATCH" && url.pathname.endsWith(`/hazards/${hazardId}`)) {
      const body = request.postDataJSON() as Record<string, unknown>;
      if (body.expected_version !== current.version) {
        await route.fulfill({
          status: 409,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "hazard_version_conflict",
              message: "Version conflict",
            },
          }),
        });
        return;
      }
      current = {
        ...current,
        title: (body.title as string) ?? current.title,
        description: (body.description as string) ?? current.description,
        version: current.version + 1,
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
      url.pathname.endsWith(`/hazards/${hazardId}/activate`)
    ) {
      current = { ...current, status: "active", version: current.version + 1 };
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

  await login(page);
  await page.goto("/safety/hazards");
  await expect(page.getByRole("heading", { name: "Опасности" })).toBeVisible();
  await page.getByRole("link", { name: "Создать опасность" }).first().click();
  await page.getByLabel("Код").fill("HZ-E2E");
  await page.getByLabel("Название").fill("E2E Hazard");
  await page.getByRole("button", { name: "Создать опасность" }).click();
  await expect(page.getByRole("heading", { name: "E2E Hazard" })).toBeVisible();
  await page.getByRole("button", { name: "Изменить опасность" }).click();
  await page.getByLabel("Название").fill("E2E Hazard Updated");
  await page.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(
    page.getByRole("heading", { name: "E2E Hazard Updated" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Активировать опасность" }).click();
  await page
    .getByRole("button", { name: "Активировать опасность" })
    .last()
    .click();
  await expect(page.getByLabel("Статус: Действует").first()).toBeVisible();
  await page.getByRole("link", { name: "К реестру" }).click();
  await expect(page.getByRole("heading", { name: "Опасности" })).toBeVisible();
  await expect(page.getByRole("link", { name: "HZ-E2E" })).toBeVisible();
});

test("read-only user cannot create hazards", async ({ page }) => {
  await mockAuth(page, ["hazard:read"]);
  await page.route("**/api/v1/hazards**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [],
        pagination: { total: 0, offset: 0, limit: 25 },
      }),
    });
  });
  await login(page);
  await page.goto("/safety/hazards");
  await expect(
    page.getByRole("link", { name: "Создать опасность" }),
  ).toHaveCount(0);
  await page.goto("/safety/hazards/new");
  await expect(page.getByText("Нельзя создать опасности")).toBeVisible();
});

test("unknown hazard shows not found", async ({ page }) => {
  await mockAuth(page, ["hazard:read"]);
  await page.route("**/api/v1/hazards/**", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({
        error: { code: "hazard_not_found", message: "Not found" },
      }),
    });
  });
  await login(page);
  await page.goto(`/safety/hazards/${hazardId}`);
  await expect(page.getByText("Опасность не найдена")).toBeVisible();
});

test("stale edit shows conflict dialog", async ({ page }) => {
  await mockAuth(page, [
    "hazard:read",
    "hazard:update",
    "hazard:activate",
    "risk:read",
  ]);
  const current = sampleHazard({ version: 2 });
  await page.route(`**/api/v1/hazards/${hazardId}`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ...current, version: 2 }),
      });
      return;
    }
    if (route.request().method() === "PATCH") {
      await route.fulfill({
        status: 409,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "hazard_version_conflict",
            message: "Version conflict",
          },
        }),
      });
      return;
    }
    await route.fallback();
  });
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
  await page.goto(`/safety/hazards/${hazardId}`);
  await page.getByRole("button", { name: "Изменить опасность" }).click();
  await page.getByLabel("Название").fill("Conflict title");
  await page.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(
    page.getByRole("heading", { name: "Опасность изменена в другом месте" }),
  ).toBeVisible();
});

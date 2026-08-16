import { expect, test } from "@playwright/test";

async function mockAuthApis(page: import("@playwright/test").Page) {
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
          email: "admin@example.com",
          display_name: "Admin User",
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: "22222222-2222-2222-2222-222222222222",
            organization_name: "Acme Safety",
            role: "admin",
            status: "ACTIVE",
            permissions: [
              "hazard:read",
              "risk:read",
              "risk_control:read",
              "user:read",
              "knowledge_object:read",
              "audit:read",
            ],
          },
        ],
      }),
    });
  });
  await page.route("**/api/v1/auth/logout", async (route) => {
    await route.fulfill({ status: 204, body: "" });
  });
}

test("anonymous user is redirected to login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
});

test("session restore unlocks the shell without login form", async ({
  page,
}) => {
  await mockAuthApis(page);
  await page.addInitScript(() => {
    sessionStorage.setItem("safetymain.auth.access", "access-token");
    sessionStorage.setItem("safetymain.auth.refresh", "refresh-token");
    sessionStorage.setItem("safetymain.auth.token_type", "bearer");
    sessionStorage.setItem(
      "safetymain.auth.expires_at",
      String(Date.now() + 3_600_000),
    );
    sessionStorage.setItem(
      "safetymain.auth.organization_id",
      "22222222-2222-2222-2222-222222222222",
    );
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
  await expect(page.getByText("Acme Safety")).toBeVisible();
});

test("login unlocks shell and logout returns to login", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));
  await mockAuthApis(page);

  await page.goto("/login");
  await page.getByLabel("Электронная почта").fill("admin@example.com");
  await page.getByLabel("Пароль").fill("secret-password");
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByText("Acme Safety")).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Основная" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Администрирование" }),
  ).toBeVisible();

  await page.getByRole("button", { name: /Admin User/i }).click();
  await page.getByRole("menuitem", { name: "Выйти" }).click();
  await expect(page).toHaveURL(/\/login/);
  expect(errors).toEqual([]);
});

test("permission-aware navigation hides administration", async ({ page }) => {
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
          email: "member@example.com",
          display_name: "Member User",
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: "22222222-2222-2222-2222-222222222222",
            organization_name: "Acme Safety",
            role: "member",
            status: "ACTIVE",
            permissions: ["hazard:read", "risk:read", "risk_control:read"],
          },
        ],
      }),
    });
  });

  await page.goto("/login");
  await page.getByLabel("Электронная почта").fill("member@example.com");
  await page.getByLabel("Пароль").fill("secret-password");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Администрирование" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Безопасность", exact: true }),
  ).toBeVisible();
});

import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

/** TASK-P11-012 §Verification: section → spine → scan → exclude → undo → reload. Synthetic data. */

const AXE_SOURCE = readFileSync(
  path.join(process.cwd(), "node_modules/axe-core/axe.min.js"),
  "utf8",
);

const USER_ID = "11111111-1111-1111-1111-111111111111";
const ORG_ID = "22222222-2222-2222-2222-222222222222";
const DOC_ID = "33333333-3333-4333-8333-333333333333";
const FILE_ID = "44444444-4444-4444-8444-444444444444";
const slotId = (n: number) =>
  `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;

// A one-page PDF ("Скан" is not needed; pdf.js only has to parse and render it).
const PDF = `%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R/Resources<<>>>>endobj
4 0 obj<</Length 35>>stream
0 0 1 rg 20 20 160 160 re f
endstream endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000052 00000 n 
0000000101 00000 n 
0000000188 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
272
%%EOF`;

const counts = (over: Record<string, number> = {}) => ({
  present: 0,
  review: 0,
  in_progress: 0,
  missing: 0,
  to_clarify: 0,
  excluded: 0,
  ...over,
});

function summary(code: string, n: number, over: Record<string, unknown> = {}) {
  return {
    id: slotId(n),
    code,
    subsection_code: code.split(".").slice(0, 2).join("."),
    short_title: `Место ${code}`,
    title: `Синтетическое место ${code}`,
    document_kind: "План",
    kept_on: "organization",
    obligation_level: "mandatory",
    effective_status: "missing",
    group: "missing",
    has_acknowledgement_gap: false,
    ...over,
  };
}

async function mockBackend(page: Page) {
  let excluded = false;
  let version = 2;

  const present = () =>
    summary(
      "ТрБ.01.01",
      1,
      excluded
        ? { effective_status: "excluded", group: "excluded" }
        : { effective_status: "present", group: "present" },
    );

  const detail = () => ({
    ...present(),
    section_code: "ТрБ",
    legal_basis: {
      regulation: "16-ФЗ",
      clause: "ст. 9",
      quote: "",
      source_url: null,
      confidence: "verified",
    },
    applicability_condition: "",
    review_cycle_text: "5 лет",
    review_period_months: 60,
    review_date: "2031-01-10",
    curated_status: "present",
    document_type_code: "plan",
    proposed_document_type: "",
    responsible_text: "",
    legacy_location: "",
    notes: "",
    package_code: "",
    legacy_code: "",
    exclusion: excluded
      ? {
          reason: "duplicate",
          comment: "Дублирует место в ОТ",
          excluded_by_name: "Куратор",
          excluded_at: "2026-11-06T09:00:00Z",
        }
      : null,
    current_document: {
      id: DOC_ID,
      code: "ПОТБ-1",
      title: "План обеспечения",
      status: "active",
      effective_from: "2026-01-10",
      next_review_at: null,
      approved_by_order: null,
      signed_scan: {
        file_id: FILE_ID,
        content_type: "application/pdf",
        size_bytes: PDF.length,
        uploaded_at: "2026-01-10T00:00:00Z",
      },
      working_file: null,
    },
    editions: [
      {
        id: DOC_ID,
        code: "ПОТБ-1",
        status: "active",
        effective_from: "2026-01-10",
      },
    ],
    available_actions: excluded ? ["restore"] : ["open_document", "exclude"],
    primary_action: excluded ? "restore" : "open_document",
    acknowledgement: null,
    version,
  });

  await page.route("**/api/v1/auth/login", (route) =>
    route.fulfill({
      json: {
        access_token: "a",
        refresh_token: "r",
        token_type: "bearer",
        expires_in: 3600,
      },
    }),
  );
  await page.route("**/api/v1/auth/session", (route) =>
    route.fulfill({
      json: {
        user: {
          id: USER_ID,
          email: "curator@example.com",
          display_name: "Куратор",
          status: "ACTIVE",
        },
        memberships: [
          {
            organization_id: ORG_ID,
            organization_name: "Синтетика",
            role: "admin",
            status: "ACTIVE",
            permissions: [
              "shelf:read",
              "shelf:curate",
              "compliance_document:read",
            ],
          },
        ],
      },
    }),
  );
  await page.route("**/api/v1/shelf", (route) =>
    route.fulfill({
      json: {
        sections: [
          {
            code: "ТрБ",
            number: 10,
            title: "Транспортная безопасность",
            safety_domain: "transport_security",
            total: 2,
            mandatory_total: 2,
            by_group: counts(
              excluded
                ? { missing: 1, excluded: 1 }
                : { present: 1, missing: 1 },
            ),
            readiness_percent: 50,
            strip: [
              { code: "ТрБ.01.01", group: excluded ? "excluded" : "present" },
              { code: "ТрБ.01.02", group: "missing" },
            ],
          },
        ],
        totals: {
          places: 2,
          excluded: excluded ? 1 : 0,
          by_group: counts(
            excluded ? { missing: 1, excluded: 1 } : { present: 1, missing: 1 },
          ),
          readiness_percent: 50,
        },
        evaluated_at: "2026-11-06T09:00:00Z",
        last_imported_at: "2026-11-05T09:00:00Z",
      },
    }),
  );
  await page.route("**/api/v1/shelf/sections/**", (route) =>
    route.fulfill({
      json: {
        section: {
          code: "ТрБ",
          number: 10,
          title: "Транспортная безопасность",
        },
        subsections: [
          {
            code: "ТрБ.01",
            title: "Оценка уязвимости",
            slots: [present(), summary("ТрБ.01.02", 2)],
          },
        ],
      },
    }),
  );
  await page.route(`**/api/v1/shelf/slots/${slotId(1)}`, (route) =>
    route.fulfill({ json: detail() }),
  );
  await page.route(`**/api/v1/shelf/slots/${slotId(1)}/exclude`, (route) => {
    excluded = true;
    version += 1;
    return route.fulfill({ json: detail() });
  });
  await page.route(`**/api/v1/shelf/slots/${slotId(1)}/restore`, (route) => {
    excluded = false;
    version += 1;
    return route.fulfill({ json: detail() });
  });
  await page.route(
    `**/api/v1/compliance-documents/${DOC_ID}/files/${FILE_ID}/view-url`,
    (route) =>
      route.fulfill({
        json: {
          url: "http://127.0.0.1:3100/__test/scan.pdf",
          filename: "scan.pdf",
          content_type: "application/pdf",
        },
      }),
  );
  await page.route("**/__test/scan.pdf", (route) =>
    route.fulfill({ status: 200, contentType: "application/pdf", body: PDF }),
  );
}

async function expectNoSeriousAxeViolations(page: Page) {
  await page.addScriptTag({ content: AXE_SOURCE });
  const violations = await page.evaluate(async () => {
    const result = await (
      window as unknown as {
        axe: {
          run: () => Promise<{
            violations: Array<{ id: string; impact: string }>;
          }>;
        };
      }
    ).axe.run();
    return result.violations
      .filter((item) => item.impact === "critical" || item.impact === "serious")
      .map((item) => item.id);
  });
  expect(violations).toEqual([]);
}

test("shelf: section → spine → signed scan → exclude → undo → reload", async ({
  page,
}) => {
  await mockBackend(page);
  await page.goto("/login");
  await page.getByLabel("Электронная почта").fill("curator@example.com");
  await page.getByLabel("Пароль").fill("secret-password");
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();

  await page.goto("/shelf");
  await expect(
    page.getByRole("heading", { name: "Полка документов" }),
  ).toBeVisible();
  await expectNoSeriousAxeViolations(page);

  await page.getByRole("button", { name: /Транспортная безопасность/ }).click();
  await expect(page).toHaveURL(/section=/);
  const spine = page.getByRole("button", { name: /ТрБ\.01\.01/ });
  await spine.click();
  const panel = page.getByRole("complementary", {
    name: /Синтетическое место ТрБ\.01\.01/,
  });
  await expect(panel.getByText("Скан подписанной редакции")).toBeVisible();
  await expect(panel.getByText("Страница 1 из 1")).toBeVisible();
  await expectNoSeriousAxeViolations(page);

  await panel.getByRole("button", { name: "Исключить с полки" }).click();
  await panel.getByLabel("Дублирует другое место").click();
  await panel.getByLabel(/Комментарий/).fill("Дублирует место в ОТ");
  await expectNoSeriousAxeViolations(page);
  await panel.getByRole("button", { name: "Исключить", exact: true }).click();
  const status = page
    .getByRole("status")
    .filter({ hasText: "Исключено 1 место" });
  await expect(status).toBeVisible();
  await expect(panel.getByText("Дублирует место в ОТ")).toBeVisible();

  await status.getByRole("button", { name: "Отменить" }).click();
  await expect(status).toBeHidden();
  await expect(
    panel.getByRole("link", { name: "Открыть документ" }),
  ).toBeVisible();

  const url = page.url();
  await page.reload();
  expect(page.url()).toBe(url);
  await expect(
    page.getByRole("complementary", {
      name: /Синтетическое место ТрБ\.01\.01/,
    }),
  ).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: /ТрБ\.01\.01/ })).toBeFocused();
});

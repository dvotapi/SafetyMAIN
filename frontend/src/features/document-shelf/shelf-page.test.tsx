import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { ShelfPage } from "@/features/document-shelf";
import {
  overviewFixture,
  transportSectionFixture,
} from "@/features/document-shelf/shelf-fixtures";
import { apiClient } from "@/services/api/client";
import type { ApiRequestOptions } from "@/services/api/types";

const navigation = vi.hoisted(() => ({
  params: new URLSearchParams(),
  push: vi.fn(),
  replace: vi.fn(),
}));
const auth = vi.hoisted(() => ({
  permissions: new Set(["shelf:read", "shelf:curate"]),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/shelf",
  useRouter: () => ({ push: navigation.push, replace: navigation.replace }),
  useSearchParams: () => navigation.params,
}));

vi.mock("@/hooks/auth", () => ({
  useAuth: () => ({ hasPermission: (p: string) => auth.permissions.has(p) }),
  useOrganization: () => ({
    organizationId: "org-1",
    organizationName: "Org",
    membership: null,
  }),
}));

type Responder = (options: ApiRequestOptions) => unknown;

function mockApi(responder: Responder) {
  vi.spyOn(apiClient, "request").mockImplementation(async (options) =>
    responder(options as ApiRequestOptions),
  );
}

function defaultResponder(options: ApiRequestOptions): unknown {
  if (options.path === "/api/v1/shelf") return overviewFixture();
  if (options.path.startsWith("/api/v1/shelf/sections/"))
    return transportSectionFixture();
  throw new Error(`Unexpected ${options.method} ${options.path}`);
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ShelfPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  navigation.params = new URLSearchParams();
  navigation.push.mockReset();
  navigation.replace.mockReset();
  auth.permissions = new Set(["shelf:read", "shelf:curate"]);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ShelfPage", () => {
  it("shows the header, summary and overview strips from the API", async () => {
    mockApi(defaultResponder);
    renderPage();

    expect(
      await screen.findByRole("heading", { name: "Полка документов" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /5 мест в 2 разделах · исключено 1 · реестр сверен с НПА/,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
    const rows = screen.getAllByRole("button", { expanded: false });
    expect(
      rows.map((row) => within(row).getAllByText(/./)[1]?.textContent),
    ).toEqual(["Пожарная безопасность", "Транспортная безопасность"]);
    expect(
      screen.getByRole("progressbar", { name: "Готовность полки" }),
    ).toHaveAttribute("aria-valuenow", "40");
  });

  it("opens a section with its first place and pushes the URL", async () => {
    mockApi(defaultResponder);
    renderPage();

    await userEvent.click(
      await screen.findByRole("button", { name: /Транспортная безопасность/ }),
    );

    expect(navigation.push).toHaveBeenCalledWith(
      "/shelf?section=%D0%A2%D1%80%D0%91&slot=%D0%A2%D1%80%D0%91.01.01",
      {
        scroll: false,
      },
    );
  });

  it("renders the opened shelf by subsection with accessible spines and focus tooltips", async () => {
    navigation.params = new URLSearchParams("section=ТрБ&slot=ТрБ.01.01");
    mockApi(defaultResponder);
    renderPage();

    const shelf = await screen.findByRole("region", {
      name: /Транспортная безопасность/,
    });
    expect(
      await within(shelf).findByText("Оценка уязвимости"),
    ).toBeInTheDocument();
    expect(
      within(shelf).getByText(
        /1 из 4 в порядке · 3 обязательных · исключено 1/,
      ),
    ).toBeInTheDocument();
    const spine = within(shelf).getByRole("button", { name: /ТрБ\.01\.02/ });
    expect(spine).toHaveAccessibleName(/Нет$/);
    expect(
      within(shelf).getByRole("button", { name: /ТрБ\.01\.01/ }),
    ).toHaveAttribute("aria-current", "true");

    spine.focus();
    const tooltip = await screen.findByRole("tooltip");
    expect(tooltip).toHaveTextContent("ТрБ.01.02");
    expect(tooltip).toHaveTextContent("Оценка уязвимости · План · обязателен");
    expect(spine).toHaveAttribute("aria-describedby", tooltip.id);

    await userEvent.click(spine);
    expect(navigation.push).toHaveBeenLastCalledWith(
      expect.stringContaining("slot=%D0%A2%D1%80%D0%91.01.02"),
      { scroll: false },
    );
  });

  it("dims non-matching places and hides excluded ones on request", async () => {
    navigation.params = new URLSearchParams(
      "section=ТрБ&filter=mandatory&excluded=hidden",
    );
    mockApi(defaultResponder);
    renderPage();

    const shelf = await screen.findByRole("region", {
      name: /Транспортная безопасность/,
    });
    await within(shelf).findByText("Оценка уязвимости");
    expect(
      within(shelf).queryByRole("button", { name: /ТрБ\.02\.02/ }),
    ).toBeNull();
    const conditional = within(shelf).getByRole("button", {
      name: /ТрБ\.02\.01/,
    });
    expect(conditional.parentElement?.className).toMatch(/dimmed/);
    expect(
      screen.getByRole("button", { name: "Обязательные" }),
    ).toHaveAttribute("aria-pressed", "true");

    await userEvent.click(
      screen.getByRole("button", { name: "Исключённые скрыты" }),
    );
    expect(navigation.replace).toHaveBeenCalledWith(
      "/shelf?section=%D0%A2%D1%80%D0%91&filter=mandatory",
      { scroll: false },
    );
  });

  it("invites to import when the shelf is empty", async () => {
    mockApi((options) =>
      options.path === "/api/v1/shelf"
        ? { ...overviewFixture(), sections: [] }
        : defaultResponder(options),
    );
    renderPage();

    expect(
      await screen.findByText("Загрузите реестр-полку"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Как загрузить реестр" }),
    ).toHaveAttribute(
      "href",
      expect.stringContaining("docs/guides/ShelfImport.md"),
    );
  });

  it("shows an error with retry", async () => {
    let calls = 0;
    mockApi((options) => {
      calls += 1;
      if (calls === 1) throw new Error("boom");
      return defaultResponder(options);
    });
    renderPage();

    await userEvent.click(
      await screen.findByRole("button", { name: "Повторить" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Полка документов" }),
    ).toBeInTheDocument();
  });

  it("refuses without shelf:read", async () => {
    auth.permissions = new Set();
    mockApi(defaultResponder);
    renderPage();

    expect(screen.getByText("Нет доступа")).toBeInTheDocument();
    await waitFor(() => expect(apiClient.request).not.toHaveBeenCalled());
  });

  it("has no serious accessibility violations with a shelf open", async () => {
    navigation.params = new URLSearchParams("section=ТрБ&slot=ТрБ.01.01");
    mockApi(defaultResponder);
    const { container } = renderPage();
    await screen.findByText("Оценка уязвимости");

    const results = await axe(container);
    const serious = results.violations.filter(
      (violation) =>
        violation.impact === "critical" || violation.impact === "serious",
    );
    expect(serious).toEqual([]);
  });
});

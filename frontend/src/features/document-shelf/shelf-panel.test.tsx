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

import { ToastProvider } from "@/components";
import { ShelfPage } from "@/features/document-shelf";
import {
  DOCUMENT_ID,
  FILE_ID,
  overviewFixture,
  slotDetail,
  slotSummary,
  transportSectionFixture,
} from "@/features/document-shelf/shelf-fixtures";
import type { ShelfSlotDetailDto } from "@/features/document-shelf/types/shelf-dto";
import { apiClient } from "@/services/api/client";
import { normalizeApiError } from "@/services/api/errors";
import type { ApiRequestOptions } from "@/services/api/types";

const navigation = vi.hoisted(() => ({
  params: new URLSearchParams(),
  push: vi.fn(),
  replace: vi.fn(),
}));
const auth = vi.hoisted(() => ({
  permissions: new Set([
    "shelf:read",
    "shelf:curate",
    "compliance_document:read",
  ]),
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
vi.mock("pdfjs-dist", () => ({
  GlobalWorkerOptions: { workerSrc: "" },
  getDocument: () => ({
    promise: Promise.resolve({
      numPages: 2,
      destroy: vi.fn(),
      getPage: async () => ({
        getViewport: ({ scale }: { scale: number }) => ({
          width: 600 * scale,
          height: 800 * scale,
        }),
        render: () => ({ promise: Promise.resolve(), cancel: () => undefined }),
      }),
    }),
  }),
}));

// Radix radio groups measure themselves; jsdom has no ResizeObserver.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof ResizeObserver;

const SLOT_ID = slotSummary("ТрБ.01.02").id;
const requests: ApiRequestOptions[] = [];
let detail: ShelfSlotDetailDto;

function respond(options: ApiRequestOptions): unknown {
  requests.push(options);
  const path = options.path;
  if (path === "/api/v1/shelf") return overviewFixture();
  if (path.startsWith("/api/v1/shelf/sections/"))
    return transportSectionFixture();
  if (path.startsWith("/api/v1/shelf/slots?")) {
    return { items: [slotSummary("ТрБ.02.01", { title: "Найденное место" })] };
  }
  if (path === `/api/v1/shelf/slots/${SLOT_ID}` && options.method === "GET")
    return detail;
  if (path.endsWith("/exclude")) {
    const body = options.body as { comment: string };
    if (body.comment === "сервер") {
      throw normalizeApiError({
        status: 422,
        body: { error: { code: "comment_too_short", message: "short" } },
      });
    }
    return slotDetail("ТрБ.01.02", {
      effective_status: "excluded",
      group: "excluded",
      version: 4,
    });
  }
  if (path.endsWith("/develop"))
    return { document_id: DOCUMENT_ID, slot: detail };
  if (path.endsWith("/restore")) return slotDetail("ТрБ.01.02");
  if (path === "/api/v1/shelf/slots/bulk-exclude") return { items: [] };
  if (path.startsWith("/api/v1/shelf/slots/") && options.method === "GET") {
    const id = path.split("/").pop()!;
    return slotDetail("ТрБ.01.01", { id, version: 7 });
  }
  if (path.endsWith("/view-url")) {
    return {
      url: "https://storage.test/scan.pdf",
      filename: "scan.pdf",
      content_type: "application/pdf",
    };
  }
  throw new Error(`Unexpected ${options.method} ${path}`);
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <ShelfPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  requests.length = 0;
  detail = slotDetail("ТрБ.01.02");
  navigation.params = new URLSearchParams("section=ТрБ&slot=ТрБ.01.02");
  navigation.push.mockReset();
  navigation.replace.mockReset();
  auth.permissions = new Set([
    "shelf:read",
    "shelf:curate",
    "compliance_document:read",
  ]);
  vi.spyOn(apiClient, "request").mockImplementation(async (options) =>
    respond(options as ApiRequestOptions),
  );
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

async function panel() {
  return within(
    await screen.findByRole("complementary", {
      name: /Синтетическое место ТрБ\.01\.02/,
    }),
  );
}

describe("place panel", () => {
  it("shows the missing branch, details and the backend actions", async () => {
    renderPage();
    const view = await panel();

    expect(view.getByText("Место есть, документа нет")).toBeInTheDocument();
    expect(view.getByRole("link", { name: "16-ФЗ" })).toHaveAttribute(
      "href",
      "https://pravo.gov.ru/doc",
    );
    expect(
      view.getByRole("button", { name: "Разработать" }),
    ).toBeInTheDocument();
    expect(
      view.getByRole("button", { name: "Привязать документ" }),
    ).toBeInTheDocument();
    expect(
      view.getByRole("button", { name: "Исключить с полки" }),
    ).toBeInTheDocument();
  });

  it("develops a document and opens its edit page", async () => {
    renderPage();
    const view = await panel();

    await userEvent.click(view.getByRole("button", { name: "Разработать" }));

    await waitFor(() =>
      expect(navigation.push).toHaveBeenCalledWith(
        `/compliance-documents/${DOCUMENT_ID}/edit`,
      ),
    );
    const call = requests.find((item) => item.path.endsWith("/develop"));
    expect(call?.body).toEqual({ version: 3 });
  });

  it("validates the exclusion comment inline and maps the backend code to the same message", async () => {
    renderPage();
    const view = await panel();
    await userEvent.click(
      view.getByRole("button", { name: "Исключить с полки" }),
    );
    const form = within(
      view.getByRole("form", { name: "Исключить место с полки" }),
    );

    await userEvent.type(form.getByLabelText(/Комментарий/), "abc");
    await userEvent.click(form.getByRole("button", { name: "Исключить" }));
    expect(form.getByRole("alert")).toHaveTextContent(
      "Напишите, почему место не нужно",
    );
    expect(requests.some((item) => item.path.endsWith("/exclude"))).toBe(false);

    await userEvent.clear(form.getByLabelText(/Комментарий/));
    await userEvent.type(form.getByLabelText(/Комментарий/), "сервер");
    await userEvent.click(form.getByRole("button", { name: "Исключить" }));
    expect(await form.findByRole("alert")).toHaveTextContent(
      "Напишите, почему место не нужно",
    );
  });

  it("excludes with a reason and offers undo", async () => {
    renderPage();
    const view = await panel();
    await userEvent.click(
      view.getByRole("button", { name: "Исключить с полки" }),
    );
    const form = within(
      view.getByRole("form", { name: "Исключить место с полки" }),
    );
    await userEvent.click(form.getByLabelText("Дублирует другое место"));
    await userEvent.type(
      form.getByLabelText(/Комментарий/),
      "Есть такой же в ОТ",
    );
    await userEvent.click(form.getByRole("button", { name: "Исключить" }));

    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("Исключено 1 место: ТрБ.01.02");
    const call = requests.find((item) => item.path.endsWith("/exclude"));
    expect(call?.body).toEqual({
      reason: "duplicate",
      comment: "Есть такой же в ОТ",
      version: 3,
    });

    await userEvent.click(
      within(status).getByRole("button", { name: "Отменить" }),
    );
    await waitFor(() =>
      expect(requests.some((item) => item.path.endsWith("/restore"))).toBe(
        true,
      ),
    );
  });

  it("shows exclusion details without actions to a viewer", async () => {
    auth.permissions = new Set(["shelf:read"]);
    detail = slotDetail("ТрБ.01.02", {
      effective_status: "excluded",
      group: "excluded",
      exclusion: {
        reason: "condition_not_met",
        comment: "Нет объектов транспортной инфраструктуры",
        excluded_by_name: "Куратор",
        excluded_at: "2026-11-04T10:00:00Z",
      },
      available_actions: [],
      primary_action: null,
    });
    renderPage();
    const view = await panel();

    expect(
      view.getByText("Нет объектов транспортной инфраструктуры"),
    ).toBeInTheDocument();
    expect(
      view.getByText("Условие применимости не выполняется"),
    ).toBeInTheDocument();
    expect(
      view.queryByRole("button", { name: /Вернуть|Исключить/ }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Выбрать несколько" }),
    ).toBeNull();
  });

  it("shows the working file labelled as unsigned when there is no signed scan", async () => {
    detail = slotDetail("ТрБ.01.02", {
      effective_status: "present",
      group: "present",
      current_document: {
        id: DOCUMENT_ID,
        code: "ПОТБ-1",
        title: "План",
        status: "active",
        effective_from: "2026-01-10",
        next_review_at: null,
        approved_by_order: null,
        signed_scan: null,
        working_file: {
          file_id: FILE_ID,
          content_type: "application/pdf",
          size_bytes: 2048,
          uploaded_at: "2026-01-01T00:00:00Z",
        },
      },
      available_actions: ["open_document", "upload_signed_scan", "exclude"],
      primary_action: "open_document",
    });
    renderPage();
    const view = await panel();

    expect(
      view.getAllByText("Рабочий файл (без подписи)").length,
    ).toBeGreaterThan(0);
    expect(await view.findByText("Страница 1 из 2")).toBeInTheDocument();
    expect(
      view.getByRole("link", { name: "Открыть документ" }),
    ).toHaveAttribute("href", `/compliance-documents/${DOCUMENT_ID}`);
    expect(
      view.getByRole("button", { name: "Загрузить подписанный скан" }),
    ).toBeInTheDocument();
  });

  it("closes with Escape", async () => {
    renderPage();
    await panel();

    await userEvent.keyboard("{Escape}");
    expect(navigation.push).toHaveBeenCalledWith(
      "/shelf?section=%D0%A2%D1%80%D0%91",
      { scroll: false },
    );
  });

  it("has no serious accessibility violations", async () => {
    const { container } = renderPage();
    await panel();
    const results = await axe(container);
    expect(
      results.violations.filter(
        (item) => item.impact === "critical" || item.impact === "serious",
      ),
    ).toEqual([]);
  });
});

describe("bulk exclusion", () => {
  it("selects several places and excludes them with the versions shown on the shelf", async () => {
    navigation.params = new URLSearchParams("section=ТрБ");
    renderPage();
    await userEvent.click(
      await screen.findByRole("button", { name: "Выбрать несколько" }),
    );
    const shelf = screen.getByRole("region", {
      name: /Транспортная безопасность/,
    });
    await userEvent.click(
      within(shelf).getByRole("button", { name: /ТрБ\.01\.01/ }),
    );
    await userEvent.click(
      within(shelf).getByRole("button", { name: /ТрБ\.01\.02/ }),
    );
    expect(
      within(shelf).getByRole("button", { name: /ТрБ\.02\.02/ }),
    ).toBeDisabled();

    const bar = screen.getByRole("region", { name: "Выбранные места" });
    expect(bar).toHaveTextContent("Выбрано 2 места");
    await userEvent.click(
      within(bar).getByRole("button", { name: "Исключить выбранные" }),
    );
    const form = within(
      screen.getByRole("form", { name: "Исключить 2 места с полки" }),
    );
    await userEvent.type(form.getByLabelText(/Комментарий/), "Не применяется");
    await userEvent.click(form.getByRole("button", { name: "Исключить" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Исключено 2 места: ТрБ.01.01, ТрБ.01.02",
    );
    // No detail is read just before the request: a concurrent edit must conflict.
    expect(
      requests.filter(
        (item) =>
          item.method === "GET" &&
          item.path.startsWith("/api/v1/shelf/slots/") &&
          !item.path.includes("?"),
      ),
    ).toHaveLength(0);
    const call = requests.find(
      (item) => item.path === "/api/v1/shelf/slots/bulk-exclude",
    );
    expect(call?.body).toEqual({
      items: [
        { slot_id: slotSummary("ТрБ.01.01").id, version: 2 },
        { slot_id: slotSummary("ТрБ.01.02").id, version: 2 },
      ],
      reason: "not_applicable",
      comment: "Не применяется",
    });
  });
});

describe("search", () => {
  it("opens the chosen place", async () => {
    navigation.params = new URLSearchParams();
    renderPage();
    const box = await screen.findByRole("combobox", { name: "Поиск по полке" });

    await userEvent.type(box, "найд");
    const option = await screen.findByRole("option", {
      name: /Найденное место/,
    });
    await userEvent.click(option);

    expect(navigation.push).toHaveBeenCalledWith(
      "/shelf?section=%D0%A2%D1%80%D0%91&slot=%D0%A2%D1%80%D0%91.02.01",
      { scroll: false },
    );
  });
});

describe("review fixes", () => {
  it("Escape in the search box closes only the list, not the panel", async () => {
    renderPage();
    await panel();
    const box = screen.getByRole("combobox", { name: "Поиск по полке" });
    await userEvent.type(box, "найд");
    await screen.findByRole("option", { name: /Найденное место/ });

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("listbox")).toBeNull();
    expect(navigation.push).not.toHaveBeenCalled();
  });

  it("Escape in the exclusion comment keeps the panel and the text", async () => {
    renderPage();
    const view = await panel();
    await userEvent.click(
      view.getByRole("button", { name: "Исключить с полки" }),
    );
    const comment = view.getByLabelText(/Комментарий/);
    await userEvent.type(comment, "Черновик причины");

    await userEvent.keyboard("{Escape}");

    expect(navigation.push).not.toHaveBeenCalled();
    expect(comment).toHaveValue("Черновик причины");
  });

  it("moves focus into an opened form and back to its trigger", async () => {
    renderPage();
    const view = await panel();
    await userEvent.click(
      view.getByRole("button", { name: "Исключить с полки" }),
    );

    expect(
      view.getByRole("heading", { name: "Исключить место с полки" }),
    ).toHaveFocus();
    await userEvent.click(view.getByRole("button", { name: "Отмена" }));
    await waitFor(() =>
      expect(
        view.getByRole("button", { name: "Исключить с полки" }),
      ).toHaveFocus(),
    );
  });

  it("shows an undo failure and keeps only the places still excluded", async () => {
    renderPage();
    const view = await panel();
    await userEvent.click(
      view.getByRole("button", { name: "Исключить с полки" }),
    );
    await userEvent.type(
      view.getByLabelText(/Комментарий/),
      "Есть такой же в ОТ",
    );
    await userEvent.click(view.getByRole("button", { name: "Исключить" }));
    const status = await screen.findByRole("status");
    vi.mocked(apiClient.request).mockImplementation(async (options) => {
      const request = options as ApiRequestOptions;
      if (request.path.endsWith("/restore")) {
        throw normalizeApiError({
          status: 409,
          body: {
            error: { code: "shelf_slot_version_conflict", message: "conflict" },
          },
        });
      }
      return respond(request);
    });

    await userEvent.click(
      within(status).getByRole("button", { name: "Отменить" }),
    );

    expect(await within(status).findByRole("alert")).toHaveTextContent(
      "Не удалось вернуть",
    );
    expect(status).toHaveTextContent("ТрБ.01.02");
  });

  it("explains a failed upload preparation and lets the user go back", async () => {
    detail = slotDetail("ТрБ.01.02", {
      effective_status: "present",
      group: "present",
      current_document: {
        id: DOCUMENT_ID,
        code: "ПОТБ-1",
        title: "План",
        status: "active",
        effective_from: null,
        next_review_at: null,
        approved_by_order: null,
        signed_scan: null,
        working_file: null,
      },
      available_actions: ["open_document", "upload_signed_scan", "exclude"],
      primary_action: "open_document",
    });
    vi.mocked(apiClient.request).mockImplementation(async (options) => {
      const request = options as ApiRequestOptions;
      if (request.path === `/api/v1/compliance-documents/${DOCUMENT_ID}`) {
        throw normalizeApiError({
          status: 404,
          body: { error: { code: "compliance_document_not_found" } },
        });
      }
      return respond(request);
    });
    renderPage();
    const view = await panel();

    await userEvent.click(
      view.getByRole("button", { name: "Загрузить подписанный скан" }),
    );
    expect(
      await view.findByText("Не удалось открыть загрузку"),
    ).toBeInTheDocument();
    await userEvent.click(view.getByRole("button", { name: "Назад" }));
    expect(
      await view.findByRole("button", { name: "Загрузить подписанный скан" }),
    ).toHaveFocus();
  });
});

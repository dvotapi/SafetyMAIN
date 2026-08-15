import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { Button } from "@/components/primitives/Button";
import { StatusBadge } from "@/components/primitives/StatusBadge";
import { Alert } from "@/components/feedback/Feedback";
import { ThemeProvider } from "@/theme/theme-provider";
import { resolveTheme } from "@/theme/theme-mode";
import {
  normalizeApiError,
  toUserSafeMessage,
  ValidationError,
} from "@/services/api/errors";
import { getPublicEnv, resetPublicEnvCache } from "@/lib/env";
import { AppShell } from "@/layouts/AppShell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}));

vi.mock("@/features/auth/AuthProvider", async () => {
  const actual = await vi.importActual<
    typeof import("@/features/auth/AuthProvider")
  >("@/features/auth/AuthProvider");
  return {
    ...actual,
    useAuth: () => ({
      status: "authenticated",
      tokens: null,
      session: {
        user: {
          id: "u1",
          email: "admin@example.com",
          displayName: "Admin User",
          status: "ACTIVE",
        },
        memberships: [
          {
            organizationId: "o1",
            organizationName: "Acme",
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
      },
      organizationId: "o1",
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
      hasPermission: () => true,
      currentMembership: {
        organizationId: "o1",
        organizationName: "Acme",
        role: "admin",
        status: "ACTIVE",
        permissions: ["hazard:read", "user:read"],
      },
    }),
  };
});

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

beforeAll(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }),
  });
});

afterEach(() => {
  cleanup();
});

describe("theme mode", () => {
  it("resolves system preference", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
  });
});

describe("Button", () => {
  it("renders and is clickable", async () => {
    const user = userEvent.setup();
    let clicked = false;
    render(
      <Button
        type="button"
        onClick={() => {
          clicked = true;
        }}
      >
        Save
      </Button>,
    );
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(clicked).toBe(true);
  });
});

describe("StatusBadge", () => {
  it("exposes textual status not color alone", () => {
    render(<StatusBadge status="verified_ineffective" />);
    expect(
      screen.getByLabelText("Status: Verified Ineffective"),
    ).toBeInTheDocument();
    expect(screen.getByText("Verified Ineffective")).toBeInTheDocument();
  });

  it("covers required visual statuses", () => {
    const statuses = [
      "draft",
      "under_review",
      "approved",
      "active",
      "planned",
      "implemented",
      "verified_effective",
      "verified_partially_effective",
      "verified_ineffective",
      "overdue",
      "superseded",
      "archived",
      "cancelled",
    ] as const;
    for (const status of statuses) {
      const { unmount } = render(<StatusBadge status={status} />);
      expect(screen.getByLabelText(new RegExp(`Status:`))).toBeInTheDocument();
      unmount();
    }
  });
});

describe("Alert", () => {
  it("uses alert role", async () => {
    const { container } = render(
      <Alert tone="warning" title="Attention">
        Review overdue
      </Alert>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Review overdue");
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("API errors", () => {
  it("normalizes validation and conflict", () => {
    const validation = normalizeApiError({
      status: 422,
      body: {
        code: "invalid",
        message: "Bad field",
        details: { title: ["required"] },
      },
    });
    expect(validation).toBeInstanceOf(ValidationError);
    expect(toUserSafeMessage(validation)).toBe("Bad field");

    const conflict = normalizeApiError({
      status: 409,
      body: { message: "Version conflict" },
    });
    expect(conflict.kind).toBe("conflict");
  });

  it("maps tenant mismatch", () => {
    const err = normalizeApiError({
      status: 422,
      body: { code: "organization_context_mismatch", message: "Mismatch" },
    });
    expect(err.kind).toBe("tenant_context");
  });
});

describe("env", () => {
  it("validates public environment", () => {
    resetPublicEnvCache();
    process.env.NEXT_PUBLIC_APP_URL = "http://localhost:3000";
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    process.env.NEXT_PUBLIC_APP_ENV = "test";
    const env = getPublicEnv();
    expect(env.NEXT_PUBLIC_APP_ENV).toBe("test");
  });
});

describe("AppShell", () => {
  it("renders landmarks", () => {
    render(
      <ThemeProvider>
        <AppShell>
          <h1>Content</h1>
        </AppShell>
      </ThemeProvider>,
    );
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Primary" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByLabelText("Theme mode")).toBeInTheDocument();
  });
});

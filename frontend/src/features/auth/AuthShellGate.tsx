"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { LoadingState } from "@/components/feedback/Feedback";
import { useAuth } from "@/features/auth/AuthProvider";
import { AppShell } from "@/layouts/AppShell";
import { isPublicRoute } from "@/lib/navigation";

function fullPathWithSearch(): string {
  if (typeof window === "undefined") {
    return "/";
  }
  return `${window.location.pathname}${window.location.search}`;
}

export function AuthShellGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status } = useAuth();
  const publicRoute = isPublicRoute(pathname);

  useEffect(() => {
    if (status === "restoring" || status === "authenticating") {
      return;
    }
    if (publicRoute) {
      if (status === "authenticated" && pathname === "/login") {
        router.replace("/");
      }
      return;
    }
    if (status === "unauthenticated" || status === "expired") {
      const next = encodeURIComponent(fullPathWithSearch());
      router.replace(
        status === "expired"
          ? `/session-expired?next=${next}`
          : `/login?next=${next}`,
      );
    }
  }, [pathname, publicRoute, router, status]);

  if (status === "restoring") {
    return (
      <div style={{ padding: "var(--sm-space-8)" }}>
        <LoadingState label="Восстановление сеанса" />
      </div>
    );
  }

  if (publicRoute) {
    return <>{children}</>;
  }

  if (status !== "authenticated" && status !== "refreshing") {
    return (
      <div style={{ padding: "var(--sm-space-8)" }}>
        <LoadingState label="Проверка входа" />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}

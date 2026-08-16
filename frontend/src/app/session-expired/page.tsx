"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Alert, LoadingState } from "@/components/feedback/Feedback";
import { Heading, Text } from "@/components/primitives/Text";

function SessionExpiredContent() {
  const searchParams = useSearchParams();
  const next = searchParams.get("next");
  const href =
    next && next.startsWith("/")
      ? `/login?next=${encodeURIComponent(next)}`
      : "/login";

  return (
    <div
      style={{ padding: "var(--sm-space-8)", maxWidth: 560, margin: "0 auto" }}
    >
      <Heading level={1}>Сеанс истёк</Heading>
      <Alert tone="warning" title="Войдите снова">
        Сеанс завершён или токен обновления больше не действителен.
      </Alert>
      <Text tone="secondary">
        <Link href={href}>Войти</Link>
      </Text>
    </div>
  );
}

export default function SessionExpiredPage() {
  return (
    <Suspense fallback={<LoadingState label="Загрузка" />}>
      <SessionExpiredContent />
    </Suspense>
  );
}

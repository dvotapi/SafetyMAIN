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
      <Heading level={1}>Session expired</Heading>
      <Alert tone="warning" title="Please sign in again">
        Your session ended or the refresh token is no longer valid.
      </Alert>
      <Text tone="secondary">
        <Link href={href}>Sign in</Link>
      </Text>
    </div>
  );
}

export default function SessionExpiredPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading" />}>
      <SessionExpiredContent />
    </Suspense>
  );
}

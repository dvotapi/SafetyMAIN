"use client";

import { Alert } from "@/components/feedback/Feedback";
import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { Button } from "@/components/primitives/Button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <PageContainer>
      <PageHeader title="Unexpected error" />
      <Alert tone="danger" title="Unable to render this page">
        {process.env.NODE_ENV === "development"
          ? error.message
          : "Please try again. If the problem continues, contact support."}
        {error.digest ? (
          <div>
            <small>Reference: {error.digest}</small>
          </div>
        ) : null}
      </Alert>
      <div style={{ marginTop: "var(--sm-space-4)" }}>
        <Button type="button" onClick={reset}>
          Retry
        </Button>
      </div>
    </PageContainer>
  );
}

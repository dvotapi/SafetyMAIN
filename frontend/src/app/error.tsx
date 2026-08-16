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
      <PageHeader title="Непредвиденная ошибка" />
      <Alert tone="danger" title="Не удалось отобразить страницу">
        {process.env.NODE_ENV === "development"
          ? error.message
          : "Повторите попытку. Если проблема сохраняется, обратитесь в поддержку."}
        {error.digest ? (
          <div>
            <small>Код ошибки: {error.digest}</small>
          </div>
        ) : null}
      </Alert>
      <div style={{ marginTop: "var(--sm-space-4)" }}>
        <Button type="button" onClick={reset}>
          Повторить
        </Button>
      </div>
    </PageContainer>
  );
}

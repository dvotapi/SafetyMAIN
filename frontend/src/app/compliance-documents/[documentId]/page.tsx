import { Suspense } from "react";

import { LoadingState } from "@/components";
import { ComplianceDocumentObjectPage } from "@/features/compliance-documents";

export default async function Page({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка документа" />
        </div>
      }
    >
      <ComplianceDocumentObjectPage documentId={documentId} />
    </Suspense>
  );
}

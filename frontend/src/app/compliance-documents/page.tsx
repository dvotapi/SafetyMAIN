import { Suspense } from "react";

import { LoadingState } from "@/components";
import { ComplianceDocumentRegistryPage } from "@/features/compliance-documents";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка документов" />
        </div>
      }
    >
      <ComplianceDocumentRegistryPage />
    </Suspense>
  );
}

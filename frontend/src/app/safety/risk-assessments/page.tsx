import { Suspense } from "react";

import { LoadingState } from "@/components";
import { RiskAssessmentRegistryPage } from "@/features/risk-assessments";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка оценок риска" />
        </div>
      }
    >
      <RiskAssessmentRegistryPage />
    </Suspense>
  );
}

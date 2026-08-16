import { Suspense } from "react";

import { LoadingState } from "@/components";
import { RiskAssessmentObjectPage } from "@/features/risk-assessments";

export default async function Page({
  params,
}: {
  params: Promise<{ riskAssessmentId: string }>;
}) {
  const { riskAssessmentId } = await params;
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка оценки риска" />
        </div>
      }
    >
      <RiskAssessmentObjectPage riskAssessmentId={riskAssessmentId} />
    </Suspense>
  );
}

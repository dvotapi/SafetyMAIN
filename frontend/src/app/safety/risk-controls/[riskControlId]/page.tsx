import { Suspense } from "react";

import { LoadingState } from "@/components";
import { RiskControlObjectPage } from "@/features/risk-controls";

export default async function Page({
  params,
}: {
  params: Promise<{ riskControlId: string }>;
}) {
  const { riskControlId } = await params;
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Loading risk control" />
        </div>
      }
    >
      <RiskControlObjectPage riskControlId={riskControlId} />
    </Suspense>
  );
}

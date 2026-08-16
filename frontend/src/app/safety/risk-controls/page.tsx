import { Suspense } from "react";

import { LoadingState } from "@/components";
import { RiskControlRegistryPage } from "@/features/risk-controls";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Loading risk controls" />
        </div>
      }
    >
      <RiskControlRegistryPage />
    </Suspense>
  );
}

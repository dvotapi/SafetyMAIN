import { Suspense } from "react";

import { LoadingState } from "@/components";
import { HazardRegistryPage } from "@/features/hazards";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Loading hazards" />
        </div>
      }
    >
      <HazardRegistryPage />
    </Suspense>
  );
}

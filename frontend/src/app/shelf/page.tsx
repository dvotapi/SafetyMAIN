import { Suspense } from "react";

import { LoadingState } from "@/components";
import { ShelfPage } from "@/features/document-shelf";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "var(--sm-space-8)" }}>
          <LoadingState label="Загрузка полки" />
        </div>
      }
    >
      <ShelfPage />
    </Suspense>
  );
}

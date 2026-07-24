import { Skeleton } from "@/components/feedback/Feedback";
import { PageContainer } from "@/components/patterns/Page";

export default function Loading() {
  return (
    <PageContainer>
      <Skeleton height="28px" width="240px" />
      <div style={{ marginTop: "var(--sm-space-4)" }}>
        <Skeleton height="120px" />
      </div>
    </PageContainer>
  );
}

import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { Text } from "@/components/primitives/Text";

export default function PlaceholderSectionPage({ title }: { title: string }) {
  return (
    <PageContainer>
      <PageHeader title={title} />
      <Text tone="secondary">
        Placeholder route for navigation structure. Business UI is deferred to
        later tasks.
      </Text>
    </PageContainer>
  );
}

import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { Link } from "@/components/primitives/Link";
import { Text } from "@/components/primitives/Text";

export default function NotFoundPage() {
  return (
    <PageContainer>
      <PageHeader title="Not found" />
      <Text tone="secondary">
        The page you requested is unavailable. It may not exist, or you may not
        have access.
      </Text>
      <p>
        <Link href="/">Return to Overview</Link>
      </p>
    </PageContainer>
  );
}

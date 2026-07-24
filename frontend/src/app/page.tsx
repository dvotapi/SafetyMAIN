import { Alert } from "@/components/feedback/Feedback";
import {
  ContentGrid,
  PageActions,
  PageContainer,
  PageHeader,
  PageSection,
} from "@/components/patterns/Page";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Surface";
import { StatusBadge } from "@/components/primitives/StatusBadge";
import { Text } from "@/components/primitives/Text";

export default function HomePage() {
  return (
    <PageContainer>
      <PageHeader
        title="Overview"
        description={
          <Text tone="secondary">
            Frontend bootstrap shell — placeholder content only. Business
            screens are deferred.
          </Text>
        }
        actions={
          <PageActions>
            <Button variant="secondary">Notifications</Button>
            <Button>Primary action</Button>
          </PageActions>
        }
      />
      <PageSection>
        <Alert tone="info" title="Foundation ready">
          Design tokens, themes, shared primitives, and the application shell
          are available for upcoming feature work.
        </Alert>
      </PageSection>
      <PageSection>
        <ContentGrid>
          <Card>
            <Text variant="label">Sample statuses</Text>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "var(--sm-space-2)",
                marginTop: "var(--sm-space-3)",
              }}
            >
              <StatusBadge status="draft" />
              <StatusBadge status="approved" />
              <StatusBadge status="verified_effective" />
              <StatusBadge status="verified_partially_effective" />
              <StatusBadge status="overdue" />
            </div>
          </Card>
          <Card>
            <Text variant="label">Shell regions</Text>
            <Text tone="secondary" style={{ marginTop: "var(--sm-space-2)" }}>
              Top bar, left navigation, main content, organization and user
              placeholders are structural only.
            </Text>
          </Card>
        </ContentGrid>
      </PageSection>
    </PageContainer>
  );
}

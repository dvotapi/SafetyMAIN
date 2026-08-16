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
        title="Обзор"
        description={
          <Text tone="secondary">
            Базовая оболочка приложения. Предметные разделы добавляются
            поэтапно.
          </Text>
        }
        actions={
          <PageActions>
            <Button variant="secondary">Уведомления</Button>
            <Button>Основное действие</Button>
          </PageActions>
        }
      />
      <PageSection>
        <Alert tone="info" title="Основа готова">
          Токены дизайна, темы, общие компоненты и оболочка приложения готовы
          для следующих функций.
        </Alert>
      </PageSection>
      <PageSection>
        <ContentGrid>
          <Card>
            <Text variant="label">Примеры статусов</Text>
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
            <Text variant="label">Области оболочки</Text>
            <Text tone="secondary" style={{ marginTop: "var(--sm-space-2)" }}>
              Верхняя панель, боковая навигация, основная область, организация и
              пользователь образуют структуру приложения.
            </Text>
          </Card>
        </ContentGrid>
      </PageSection>
    </PageContainer>
  );
}

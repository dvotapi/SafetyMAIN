import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { Text } from "@/components/primitives/Text";

export default function PlaceholderSectionPage({ title }: { title: string }) {
  return (
    <PageContainer>
      <PageHeader title={title} />
      <Text tone="secondary">
        Заглушка маршрута для структуры навигации. Бизнес-интерфейс будет
        добавлен в следующих задачах.
      </Text>
    </PageContainer>
  );
}

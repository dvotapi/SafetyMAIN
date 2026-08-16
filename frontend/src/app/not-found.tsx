import { PageContainer, PageHeader } from "@/components/patterns/Page";
import { Link } from "@/components/primitives/Link";
import { Text } from "@/components/primitives/Text";

export default function NotFoundPage() {
  return (
    <PageContainer>
      <PageHeader title="Страница не найдена" />
      <Text tone="secondary">
        Запрошенная страница недоступна. Возможно, она не существует или у вас
        нет к ней доступа.
      </Text>
      <p>
        <Link href="/">Вернуться к обзору</Link>
      </p>
    </PageContainer>
  );
}

import Link from "next/link";

import { Alert } from "@/components/feedback/Feedback";
import { Heading, Text } from "@/components/primitives/Text";

export default function ForbiddenPage() {
  return (
    <div
      style={{ padding: "var(--sm-space-8)", maxWidth: 560, margin: "0 auto" }}
    >
      <Heading level={1}>Доступ запрещён</Heading>
      <Alert tone="danger" title="Ошибка 403">
        Недостаточно прав для просмотра этого раздела.
      </Alert>
      <Text tone="secondary">
        <Link href="/">Вернуться к обзору</Link>
      </Text>
    </div>
  );
}

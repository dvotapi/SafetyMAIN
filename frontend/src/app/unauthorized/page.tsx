import Link from "next/link";

import { Alert } from "@/components/feedback/Feedback";
import { Heading, Text } from "@/components/primitives/Text";

export default function UnauthorizedPage() {
  return (
    <div
      style={{ padding: "var(--sm-space-8)", maxWidth: 560, margin: "0 auto" }}
    >
      <Heading level={1}>Требуется вход</Heading>
      <Alert tone="warning" title="Ошибка 401">
        Войдите, чтобы продолжить.
      </Alert>
      <Text tone="secondary">
        <Link href="/login">Перейти ко входу</Link>
      </Text>
    </div>
  );
}

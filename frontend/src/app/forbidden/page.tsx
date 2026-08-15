import Link from "next/link";

import { Alert } from "@/components/feedback/Feedback";
import { Heading, Text } from "@/components/primitives/Text";

export default function ForbiddenPage() {
  return (
    <div
      style={{ padding: "var(--sm-space-8)", maxWidth: 560, margin: "0 auto" }}
    >
      <Heading level={1}>Access denied</Heading>
      <Alert tone="danger" title="403 Forbidden">
        You do not have permission to view this area.
      </Alert>
      <Text tone="secondary">
        <Link href="/">Return to Overview</Link>
      </Text>
    </div>
  );
}

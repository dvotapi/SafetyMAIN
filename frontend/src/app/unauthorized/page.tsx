import Link from "next/link";

import { Alert } from "@/components/feedback/Feedback";
import { Heading, Text } from "@/components/primitives/Text";

export default function UnauthorizedPage() {
  return (
    <div
      style={{ padding: "var(--sm-space-8)", maxWidth: 560, margin: "0 auto" }}
    >
      <Heading level={1}>Authentication required</Heading>
      <Alert tone="warning" title="401 Unauthorized">
        You need to sign in to continue.
      </Alert>
      <Text tone="secondary">
        <Link href="/login">Go to sign in</Link>
      </Text>
    </div>
  );
}

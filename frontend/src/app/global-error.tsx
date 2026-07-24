"use client";

import { Button } from "@/components/primitives/Button";
import { Text } from "@/components/primitives/Text";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          padding: 24,
          background: "#F5F7F9",
          color: "#0E1418",
        }}
      >
        <h1>Something went wrong</h1>
        <Text as="p">
          An unexpected error occurred. You can try again.
          {process.env.NODE_ENV === "development" ? (
            <span> {error.message}</span>
          ) : null}
        </Text>
        {error.digest ? (
          <Text as="p" tone="muted" variant="caption">
            Reference: {error.digest}
          </Text>
        ) : null}
        <Button type="button" onClick={reset}>
          Retry
        </Button>
      </body>
    </html>
  );
}

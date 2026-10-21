"use client";

import { Card, Heading, LoadingState, Text } from "@/components";

import type { DocumentFileDto } from "@/features/compliance-documents/types/compliance-documents-dto";

function formatDate(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function ComplianceDocumentVersions({
  items,
  loading,
}: {
  items: DocumentFileDto[];
  loading: boolean;
}) {
  return (
    <Card>
      <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
        <Heading level={3}>Версии файлов</Heading>
        {loading ? (
          <LoadingState label="Загрузка версий" />
        ) : items.length === 0 ? (
          <Text tone="muted">Версий пока нет.</Text>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {items.map((file) => (
              <li
                key={file.id}
                style={{
                  display: "grid",
                  gap: "var(--sm-space-1)",
                  padding: "var(--sm-space-2) 0",
                  borderBottom: "1px solid var(--sm-color-border-subtle)",
                }}
              >
                <Text as="span">{file.original_filename}</Text>
                <Text as="span" tone="muted" variant="caption">
                  {formatDate(file.uploaded_at)} · {file.content_type} ·{" "}
                  {file.size_bytes} Б
                </Text>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}

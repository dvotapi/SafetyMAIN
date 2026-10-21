"use client";

import Link from "next/link";

import { Card, Heading, Text } from "@/components";

import type { ComplianceDocument } from "@/features/compliance-documents/types/compliance-documents-dto";

function Row({ label, documentId }: { label: string; documentId: string }) {
  return (
    <div
      style={{
        display: "flex",
        gap: "var(--sm-space-3)",
        alignItems: "baseline",
      }}
    >
      <Text tone="muted" variant="caption" style={{ minWidth: 140 }}>
        {label}
      </Text>
      <Link href={`/compliance-documents/${documentId}`}>{documentId}</Link>
    </div>
  );
}

export function ComplianceDocumentCrosslinks({
  document,
}: {
  document: ComplianceDocument;
}) {
  const hasAny =
    document.supersedes_document_id ||
    document.superseded_by_document_id ||
    document.approved_by_document_id;
  if (!hasAny) {
    return null;
  }
  return (
    <Card>
      <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
        <Heading level={3}>Связи с другими документами</Heading>
        {document.approved_by_document_id ? (
          <Row
            label="Утверждён приказом"
            documentId={document.approved_by_document_id}
          />
        ) : null}
        {document.supersedes_document_id ? (
          <Row
            label="Замещает редакцию"
            documentId={document.supersedes_document_id}
          />
        ) : null}
        {document.superseded_by_document_id ? (
          <Row
            label="Замещён редакцией"
            documentId={document.superseded_by_document_id}
          />
        ) : null}
      </div>
    </Card>
  );
}

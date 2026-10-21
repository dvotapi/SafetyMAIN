"use client";

import { useState } from "react";

import { Alert, Button, Card, Heading, KeyValue, Text } from "@/components";

import { getComplianceDocumentDownloadUrl } from "@/features/compliance-documents/api/compliance-documents-api";
import type { DocumentFileDto } from "@/features/compliance-documents/types/compliance-documents-dto";
import { toUserSafeMessage } from "@/services/api/errors";

function formatBytes(size: number): string {
  if (size < 1024) return `${size} Б`;
  const kb = size / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} КБ`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} МБ`;
}

export function ComplianceDocumentFilePreview({
  documentId,
  currentFile,
  canDownload,
}: {
  documentId: string;
  currentFile: DocumentFileDto | null;
  canDownload: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    setLoading(true);
    setError(null);
    try {
      const descriptor = await getComplianceDocumentDownloadUrl(documentId);
      // Presigned URL responses carry Content-Disposition: attachment —
      // navigating to the URL triggers the browser's own download.
      window.location.href = descriptor.url;
    } catch (cause) {
      setError(toUserSafeMessage(cause));
    } finally {
      setLoading(false);
    }
  }

  if (!currentFile) {
    return (
      <Card>
        <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
          <Heading level={3}>Файл документа</Heading>
          <Text tone="muted">
            Файл не прикреплён. Прикрепление файла доступно только в статусе
            «Черновик».
          </Text>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
        <Heading level={3}>Текущий файл</Heading>
        <KeyValue label="Имя файла" value={currentFile.original_filename} />
        <KeyValue label="MIME" value={currentFile.content_type} />
        <KeyValue label="Размер" value={formatBytes(currentFile.size_bytes)} />
        <KeyValue
          label="SHA-256"
          value={
            <code style={{ wordBreak: "break-all" }}>{currentFile.sha256}</code>
          }
        />
        {canDownload ? (
          <div>
            <Button
              type="button"
              variant="primary"
              size="sm"
              loading={loading}
              onClick={handleDownload}
            >
              Скачать файл
            </Button>
          </div>
        ) : null}
        {error ? (
          <Alert tone="danger" title="Не удалось получить ссылку">
            {error}
          </Alert>
        ) : null}
      </div>
    </Card>
  );
}

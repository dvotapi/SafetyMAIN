"use client";

import { KeyValue, PropertyGrid } from "@/components";

import type {
  ComplianceDocument,
  DocumentTypeDto,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import {
  complianceDocumentSourceLabel,
  documentSubjectKindLabel,
  safetyDomainLabel,
} from "@/features/compliance-documents/utils/status";
import { formatDateOnly } from "@/utils/format-date";

export function ComplianceDocumentProperties({
  document,
  documentType,
}: {
  document: ComplianceDocument;
  documentType: DocumentTypeDto | undefined;
}) {
  return (
    <PropertyGrid>
      <KeyValue label="Код" value={document.code} />
      <KeyValue
        label="Тип документа"
        value={documentType ? documentType.title_ru : "—"}
      />
      <KeyValue
        label="Домен безопасности"
        value={
          documentType ? safetyDomainLabel(documentType.safety_domain) : "—"
        }
      />
      <KeyValue
        label="Субъект"
        value={documentSubjectKindLabel(document.subject_kind)}
      />
      <KeyValue label="Издан" value={formatDateOnly(document.issued_at)} />
      <KeyValue
        label="Действует с"
        value={formatDateOnly(document.effective_from)}
      />
      <KeyValue
        label="Следующий пересмотр"
        value={formatDateOnly(document.next_review_at)}
      />
      <KeyValue
        label="Источник"
        value={complianceDocumentSourceLabel(document.source)}
      />
      <KeyValue label="Версия" value={String(document.version)} />
      {document.archive_reason ? (
        <KeyValue
          label="Причина архивирования"
          value={document.archive_reason}
        />
      ) : null}
      {document.notes ? (
        <KeyValue label="Примечания" value={document.notes} />
      ) : null}
    </PropertyGrid>
  );
}

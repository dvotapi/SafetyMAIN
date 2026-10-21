import type { VisualStatus } from "@/components";

import type {
  ComplianceDocumentSource,
  ComplianceDocumentStatus,
  DocumentSubjectKind,
  SafetyDomain,
} from "@/features/compliance-documents/types/compliance-documents-dto";

const STATUS_LABELS: Record<ComplianceDocumentStatus, string> = {
  draft: "Черновик",
  approved: "Утверждён",
  active: "Действует",
  under_review: "На пересмотре",
  superseded: "Замещён",
  archived: "Архив",
};

const STATUS_VISUAL: Record<ComplianceDocumentStatus, VisualStatus> = {
  draft: "draft",
  approved: "approved",
  active: "active",
  under_review: "under_review",
  superseded: "superseded",
  archived: "archived",
};

const SUBJECT_KIND_LABELS: Record<DocumentSubjectKind, string> = {
  organization: "Организация",
  employee: "Работник",
  asset: "Актив",
};

const SAFETY_DOMAIN_LABELS: Record<SafetyDomain, string> = {
  occupational: "Охрана труда",
  industrial: "Промышленная безопасность",
  labour: "Трудовое право",
  fire: "Пожарная безопасность",
  environmental: "Экология",
  road: "БДД",
  dangerous_goods: "Опасные грузы",
};

const SOURCE_LABELS: Record<ComplianceDocumentSource, string> = {
  manual: "Ручной ввод",
  generated: "Сгенерирован",
  hr_form: "Из HR-формы",
};

export function complianceDocumentStatusLabel(
  status: ComplianceDocumentStatus,
): string {
  return STATUS_LABELS[status];
}

export function complianceDocumentStatusToVisual(
  status: ComplianceDocumentStatus,
): VisualStatus {
  return STATUS_VISUAL[status];
}

export function documentSubjectKindLabel(kind: DocumentSubjectKind): string {
  return SUBJECT_KIND_LABELS[kind];
}

export function safetyDomainLabel(domain: SafetyDomain): string {
  return SAFETY_DOMAIN_LABELS[domain];
}

export function complianceDocumentSourceLabel(
  source: ComplianceDocumentSource,
): string {
  return SOURCE_LABELS[source];
}

/**
 * Backend-authoritative `is_review_due` is only meaningful while the document
 * is still in force. Hiding it for terminal states keeps the warning cue honest.
 */
export function shouldShowReviewDueWarning(
  status: ComplianceDocumentStatus,
  isReviewDue: boolean,
): boolean {
  return isReviewDue && (status === "active" || status === "under_review");
}

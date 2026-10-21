import type { ComplianceDocumentFormValues } from "@/features/compliance-documents/schemas/compliance-document-form-schema";
import type {
  ComplianceDocumentDto,
  CreateComplianceDocumentRequest,
  DocumentApplicabilityPayload,
  UpdateComplianceDocumentRequest,
} from "@/features/compliance-documents/types/compliance-documents-dto";

function emptyToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : trimmed;
}

function buildApplicability(
  values: ComplianceDocumentFormValues,
): DocumentApplicabilityPayload {
  return {
    positions: values.positions,
    work_types: values.work_types,
    departments: values.departments,
    // asset_ids is not editable in the current UI; pass through what the
    // server returned so saving a draft never silently drops linked assets.
    asset_ids: values.asset_ids,
  };
}

export function formValuesToCreateRequest(
  values: ComplianceDocumentFormValues,
): CreateComplianceDocumentRequest {
  const body: CreateComplianceDocumentRequest = {
    document_type_id: values.document_type_id,
    code: values.code.trim(),
    title: values.title.trim(),
    applicability: buildApplicability(values),
    source: "manual",
    notes: values.notes,
  };
  const subject = emptyToNull(values.subject_id);
  if (subject !== null) body.subject_id = subject;
  const issued = emptyToNull(values.issued_at);
  if (issued !== null) body.issued_at = issued;
  const effective = emptyToNull(values.effective_from);
  if (effective !== null) body.effective_from = effective;
  const nextReview = emptyToNull(values.next_review_at);
  if (nextReview !== null) body.next_review_at = nextReview;
  const approvedBy = emptyToNull(values.approved_by_document_id);
  if (approvedBy !== null) body.approved_by_document_id = approvedBy;
  const supersedes = emptyToNull(values.supersedes_document_id);
  if (supersedes !== null) body.supersedes_document_id = supersedes;
  return body;
}

export function formValuesToUpdateRequest(
  values: ComplianceDocumentFormValues,
  expectedVersion: number,
): UpdateComplianceDocumentRequest {
  return {
    expected_version: expectedVersion,
    code: values.code.trim(),
    title: values.title.trim(),
    issued_at: emptyToNull(values.issued_at),
    effective_from: emptyToNull(values.effective_from),
    next_review_at: emptyToNull(values.next_review_at),
    approved_by_document_id: emptyToNull(values.approved_by_document_id),
    supersedes_document_id: emptyToNull(values.supersedes_document_id),
    applicability: buildApplicability(values),
    notes: values.notes,
  };
}

export function complianceDocumentToFormValues(
  document: ComplianceDocumentDto,
): ComplianceDocumentFormValues {
  return {
    document_type_id: document.document_type_id,
    code: document.code,
    title: document.title,
    subject_id: document.subject_id ?? "",
    issued_at: document.issued_at ?? "",
    effective_from: document.effective_from ?? "",
    next_review_at: document.next_review_at ?? "",
    approved_by_document_id: document.approved_by_document_id ?? "",
    supersedes_document_id: document.supersedes_document_id ?? "",
    positions: document.applicability.positions,
    work_types: document.applicability.work_types,
    departments: document.applicability.departments,
    asset_ids: document.applicability.asset_ids,
    notes: document.notes,
  };
}

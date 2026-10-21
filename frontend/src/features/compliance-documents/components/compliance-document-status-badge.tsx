"use client";

import { StatusBadge } from "@/components";

import {
  complianceDocumentStatusLabel,
  complianceDocumentStatusToVisual,
} from "@/features/compliance-documents/utils/status";
import type { ComplianceDocumentStatus } from "@/features/compliance-documents/types/compliance-documents-dto";

export function ComplianceDocumentStatusBadge({
  status,
}: {
  status: ComplianceDocumentStatus;
}) {
  return (
    <StatusBadge
      status={complianceDocumentStatusToVisual(status)}
      label={complianceDocumentStatusLabel(status)}
    />
  );
}

"use client";

import { Button } from "@/components";

import type { ComplianceDocument } from "@/features/compliance-documents/types/compliance-documents-dto";
import type { ComplianceDocumentCapabilities } from "@/features/compliance-documents/hooks/use-compliance-document-permissions";

export type LifecycleAction =
  | "approve"
  | "activate"
  | "start_review"
  | "complete_review"
  | "archive"
  | "restore";

interface Props {
  document: ComplianceDocument;
  capabilities: ComplianceDocumentCapabilities;
  busyAction: LifecycleAction | null;
  onApprove: () => void;
  onActivate: () => void;
  onStartReview: () => void;
  onCompleteReviewOpen: () => void;
  onArchiveOpen: () => void;
  onRestoreOpen: () => void;
}

export function ComplianceDocumentLifecycleActions({
  document,
  capabilities,
  busyAction,
  onApprove,
  onActivate,
  onStartReview,
  onCompleteReviewOpen,
  onArchiveOpen,
  onRestoreOpen,
}: Props) {
  const status = document.status;
  const buttons: Array<{
    key: LifecycleAction;
    label: string;
    onClick: () => void;
    show: boolean;
  }> = [
    {
      key: "approve",
      label: "Утвердить",
      onClick: onApprove,
      show: status === "draft" && capabilities.canApprove,
    },
    {
      key: "activate",
      label: "Ввести в действие",
      onClick: onActivate,
      show: status === "approved" && capabilities.canActivate,
    },
    {
      key: "start_review",
      label: "Начать пересмотр",
      onClick: onStartReview,
      show: status === "active" && capabilities.canUpdate,
    },
    {
      key: "complete_review",
      label: "Завершить пересмотр",
      onClick: onCompleteReviewOpen,
      show: status === "under_review" && capabilities.canActivate,
    },
    {
      key: "archive",
      label: "В архив",
      onClick: onArchiveOpen,
      show:
        capabilities.canArchive &&
        status !== "archived" &&
        status !== "superseded",
    },
    {
      key: "restore",
      label: "Восстановить из архива",
      onClick: onRestoreOpen,
      show: status === "archived" && capabilities.canArchive,
    },
  ];

  const visible = buttons.filter((b) => b.show);
  if (visible.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        gap: "var(--sm-space-2)",
        flexWrap: "wrap",
      }}
    >
      {visible.map((btn) => (
        <Button
          key={btn.key}
          type="button"
          variant={btn.key === "archive" ? "secondary" : "primary"}
          size="sm"
          loading={busyAction === btn.key}
          disabled={busyAction !== null && busyAction !== btn.key}
          onClick={btn.onClick}
        >
          {btn.label}
        </Button>
      ))}
    </div>
  );
}

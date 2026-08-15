"use client";

import type { ReactNode } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components";

/**
 * Generic command dialog shell shared by all risk control lifecycle
 * commands. Callers supply the body (`children`) — e.g. a single required
 * reason `TextArea` for reason-only commands — and own validation of that
 * body before invoking `onConfirm`.
 */
export function RiskControlCommandDialog({
  open,
  onOpenChange,
  title,
  version,
  children,
  errorMessage,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  loading = false,
  confirmDisabled = false,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  version: number;
  children?: ReactNode;
  errorMessage?: string | null;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  loading?: boolean;
  confirmDisabled?: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader
          title={title}
          description={`This action uses version ${version}.`}
        />
        <DialogBody>
          <div style={{ display: "grid", gap: 12 }}>
            {children}
            {errorMessage ? (
              <Alert tone="danger" title="Command failed">
                {errorMessage}
              </Alert>
            ) : null}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            {cancelLabel}
          </Button>
          <Button
            variant="primary"
            loading={loading}
            disabled={loading || confirmDisabled}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

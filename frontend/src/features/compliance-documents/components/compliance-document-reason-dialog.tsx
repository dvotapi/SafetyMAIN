"use client";

import { useEffect, useRef, useState } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Label,
  TextArea,
} from "@/components";

export function ComplianceDocumentReasonDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  loading,
  errorMessage,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel: string;
  loading: boolean;
  errorMessage?: string | null;
  onConfirm: (reason: string) => void;
}) {
  const [reason, setReason] = useState("");
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      lastFocusedRef.current = document.activeElement as HTMLElement | null;
      setReason("");
    }
  }, [open]);

  const trimmed = reason.trim();
  const canConfirm = trimmed.length > 0 && !loading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          lastFocusedRef.current?.focus();
        }}
      >
        <DialogHeader title={title} {...(description ? { description } : {})} />
        <DialogBody>
          <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
            <Label htmlFor="compliance-document-reason">Причина</Label>
            <TextArea
              id="compliance-document-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Укажите причину"
            />
            {errorMessage ? (
              <Alert tone="danger" title="Не удалось выполнить действие">
                {errorMessage}
              </Alert>
            ) : null}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button
            variant="primary"
            loading={loading}
            disabled={!canConfirm}
            onClick={() => onConfirm(trimmed)}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

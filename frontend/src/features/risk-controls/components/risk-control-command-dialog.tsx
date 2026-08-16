"use client";

import { type ReactNode, useEffect, useRef } from "react";

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
 *
 * Focus restore: every caller opens this dialog from a plain `Button`
 * click (setting external `open` state) rather than through Radix's
 * `Dialog.Trigger`. Radix's own close-focus logic only ever restores
 * focus to `Dialog.Trigger`'s ref — with no trigger registered, it would
 * silently drop focus to `<body>` on close. We track the element that had
 * focus when the dialog opened and restore it ourselves via
 * `onCloseAutoFocus`, so keyboard and screen-reader users land back on the
 * button that opened the dialog, not at the top of the document.
 */
export function RiskControlCommandDialog({
  open,
  onOpenChange,
  title,
  version,
  children,
  errorMessage,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
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
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      lastFocusedRef.current = document.activeElement as HTMLElement | null;
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          lastFocusedRef.current?.focus();
        }}
      >
        <DialogHeader
          title={title}
          description={`Действие выполняется для версии ${version}.`}
        />
        <DialogBody>
          <div style={{ display: "grid", gap: 12 }}>
            {children}
            {errorMessage ? (
              <Alert tone="danger" title="Не удалось выполнить команду">
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

"use client";

import { type ReactNode } from "react";

import { Button } from "@/components/primitives/Button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components/dialogs/Dialog";

export interface ConfirmationDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  loading?: boolean;
}

export function ConfirmationDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  loading,
}: ConfirmationDialogProps) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <Dialog {...rootProps}>
      <DialogContent>
        <DialogHeader title={title} description={description} />
        <DialogFooter>
          <Button
            variant="secondary"
            onClick={() => {
              onCancel?.();
              onOpenChange?.(false);
            }}
          >
            {cancelLabel}
          </Button>
          <Button
            variant="primary"
            {...(loading ? { loading: true } : {})}
            onClick={() => {
              onConfirm?.();
              onOpenChange?.(false);
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function DeleteConfirmation({
  open,
  onOpenChange,
  title = "Delete item",
  description = "This action cannot be undone.",
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  loading,
}: ConfirmationDialogProps) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <Dialog {...rootProps}>
      <DialogContent>
        <DialogHeader title={title} description={description} />
        <DialogFooter>
          <Button
            variant="secondary"
            onClick={() => {
              onCancel?.();
              onOpenChange?.(false);
            }}
          >
            {cancelLabel}
          </Button>
          <Button
            variant="danger"
            {...(loading ? { loading: true } : {})}
            onClick={() => {
              onConfirm?.();
              onOpenChange?.(false);
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function InfoDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  actionLabel = "Close",
  onAction,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <Dialog {...rootProps}>
      <DialogContent>
        <DialogHeader title={title} description={description} />
        {children ? <DialogBody>{children}</DialogBody> : null}
        <DialogFooter>
          <Button
            variant="primary"
            onClick={() => {
              onAction?.();
              onOpenChange?.(false);
            }}
          >
            {actionLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function WarningDialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  confirmLabel = "Continue",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <Dialog {...rootProps}>
      <DialogContent>
        <DialogHeader title={title} description={description} />
        {children ? <DialogBody>{children}</DialogBody> : null}
        <DialogFooter>
          <Button
            variant="secondary"
            onClick={() => {
              onCancel?.();
              onOpenChange?.(false);
            }}
          >
            {cancelLabel}
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              onConfirm?.();
              onOpenChange?.(false);
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

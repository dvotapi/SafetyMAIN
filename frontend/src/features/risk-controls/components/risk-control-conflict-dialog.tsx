"use client";

import { useEffect, useRef } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components";

export type RiskControlConflictVariant =
  "version_conflict" | "duplicate_materialization";

/** Backend error codes that select the duplicate-materialization copy. */
const DUPLICATE_MATERIALIZATION_CODE = "risk_control_already_materialized";

/**
 * Chooses the conflict dialog variant from the API error code, never from
 * HTTP status alone (both variants surface as 409 Conflict).
 */
export function riskControlConflictVariantFromCode(
  code?: string,
): RiskControlConflictVariant {
  return code === DUPLICATE_MATERIALIZATION_CODE
    ? "duplicate_materialization"
    : "version_conflict";
}

const VARIANT_COPY: Record<
  RiskControlConflictVariant,
  { title: string; description: string; alertTitle: string }
> = {
  version_conflict: {
    title: "Risk control changed elsewhere",
    description:
      "Another user updated this control. Your changes were not saved.",
    alertTitle: "Version conflict",
  },
  duplicate_materialization: {
    title: "Controls already materialized",
    description:
      "One or more proposed controls already have a risk control. Materialization is all-or-nothing, so nothing was created. Reload to see the current controls.",
    alertTitle: "Already materialized",
  },
};

export function RiskControlConflictDialog({
  open,
  onOpenChange,
  onReload,
  loading,
  variant = "version_conflict",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReload: () => void;
  loading?: boolean;
  variant?: RiskControlConflictVariant;
}) {
  const copy = VARIANT_COPY[variant];
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
        <DialogHeader title={copy.title} description={copy.description} />
        <DialogBody>
          <Alert tone="warning" title={copy.alertTitle}>
            Reload the latest version, then re-apply your edits. The command
            will not retry automatically.
          </Alert>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Keep my draft
          </Button>
          <Button
            variant="primary"
            {...(loading ? { loading: true } : {})}
            onClick={() => {
              onReload();
              onOpenChange(false);
            }}
          >
            Reload latest
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

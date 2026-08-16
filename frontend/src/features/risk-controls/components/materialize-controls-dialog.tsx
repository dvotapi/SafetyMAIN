"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  Alert,
  BlockingReason,
  Button,
  Checkbox,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Text,
  useToast,
} from "@/components";
import { useMaterializeRiskControlsMutation } from "@/features/risk-controls/api/risk-control-mutations";
import { useRiskControlListQuery } from "@/features/risk-controls/api/risk-control-queries";
import {
  RiskControlConflictDialog,
  riskControlConflictVariantFromCode,
  type RiskControlConflictVariant,
} from "@/features/risk-controls/components/risk-control-conflict-dialog";
import { useRiskControlPermissions } from "@/features/risk-controls/hooks/use-risk-control-permissions";
import type { RiskControl } from "@/features/risk-controls/types/risk-control-types";
import { formatRiskControlEnumLabel } from "@/features/risk-controls/utils/risk-control-status";
import {
  ConflictError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

/**
 * Statuses this dialog understands. Kept local (rather than importing the
 * Risk Assessment feature's `RiskAssessmentStatusDto`) so this file never
 * crosses the feature boundary — the caller's `assessment.status` is
 * structurally compatible without an import.
 */
export type MaterializableAssessmentStatus =
  "draft" | "under_review" | "approved" | "superseded" | "archived";

/**
 * Structural shape of a proposed control the assessment supplies. Kept
 * local for the same reason as `MaterializableAssessmentStatus` — the
 * caller passes `assessment.controls` (Risk Assessment's `ControlMeasure[]`),
 * which satisfies this shape without an import.
 */
export interface MaterializeProposedControl {
  id: string | null;
  controlType: string;
  description: string;
}

function readLocation(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map(String);
  }
  return [];
}

function readViolationMessage(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

/** Mirrors `useRiskControlCommand`'s violation-flattening for inline 422s. */
function flattenValidationError(error: ValidationError): string {
  const details = error.details;
  if (details && typeof details === "object" && !Array.isArray(details)) {
    const violations = (details as Record<string, unknown>)["violations"];
    if (Array.isArray(violations) && violations.length > 0) {
      const lines = violations
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }
          const violation = item as Record<string, unknown>;
          const location = readLocation(
            violation["location"] ?? violation["loc"],
          );
          const last =
            location.length > 0 ? location[location.length - 1] : null;
          const message =
            readViolationMessage(violation["message"]) ??
            readViolationMessage(violation["msg"]);
          if (!last || !message) {
            return null;
          }
          return `${last}: ${message}`;
        })
        .filter((line): line is string => Boolean(line));
      if (lines.length > 0) {
        return lines.join("; ");
      }
    }
  }
  return toUserSafeMessage(error);
}

/**
 * Owned entirely by the Risk Controls feature so the Risk Assessment
 * feature never touches Risk Control internals (types, mutations,
 * mappers). Renders both its own trigger button and the dialog — callers
 * only need to drop `<MaterializeControlsDialog .../>` into an actions
 * slot and manage the `open` boolean.
 *
 * Never mutates the assessment client-side: the assessment object is
 * never written to. On success it relies on
 * `useMaterializeRiskControlsMutation`'s own invalidation (Risk Control
 * lists + the assessment's related-controls query via
 * `invalidateAssessmentRelatedControls`) plus the optional `onSuccess`
 * callback for the caller's own refresh.
 */
export function MaterializeControlsDialog({
  riskAssessmentId,
  assessmentStatus,
  proposedControls,
  open,
  onOpenChange,
  onSuccess,
}: {
  riskAssessmentId: string;
  assessmentStatus: MaterializableAssessmentStatus;
  proposedControls: MaterializeProposedControl[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (controls: RiskControl[]) => void;
}) {
  const capabilities = useRiskControlPermissions();
  const { toast } = useToast();
  const mutation = useMaterializeRiskControlsMutation(riskAssessmentId);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [allowUnderReview, setAllowUnderReview] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [conflictVariant, setConflictVariant] =
    useState<RiskControlConflictVariant>("duplicate_materialization");
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  // Full RiskControl records (not the Risk Assessment feature's lite
  // summary) so `source.sourceControlReference` is available to derive
  // which proposed controls already have a materialized Risk Control.
  const materializedQuery = useRiskControlListQuery(
    {
      risk_assessment_id: riskAssessmentId,
      include_terminal: true,
      limit: 100,
    },
    open,
  );

  const materializedSourceRefs = useMemo(() => {
    const refs = new Set<string>();
    for (const control of materializedQuery.data?.items ?? []) {
      if (control.source.sourceControlReference) {
        refs.add(control.source.sourceControlReference);
      }
    }
    return refs;
  }, [materializedQuery.data]);

  useEffect(() => {
    if (open) {
      lastFocusedRef.current = document.activeElement as HTMLElement | null;
    }
  }, [open]);

  if (!capabilities.canMaterialize) {
    return null;
  }

  const isApproved = assessmentStatus === "approved";
  const isUnderReview = assessmentStatus === "under_review";
  const isBlocked = !isApproved && !isUnderReview;
  const enabled = isApproved || (isUnderReview && allowUnderReview);

  function resetState() {
    setSelectedIds(new Set());
    setAllowUnderReview(false);
    setSubmitError(null);
  }

  function handleOpenChange(next: boolean) {
    if (!next) {
      resetState();
    }
    onOpenChange(next);
  }

  function toggleSelected(id: string, checked: boolean) {
    setSelectedIds((previous) => {
      const next = new Set(previous);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }

  async function handleConfirm() {
    setSubmitError(null);
    try {
      const controls = await mutation.mutateAsync({
        control_ids: selectedIds.size > 0 ? Array.from(selectedIds) : null,
        allow_under_review: isUnderReview && allowUnderReview,
      });
      const codes = controls.map((control) => control.code).join(", ");
      toast({
        tone: "success",
        title: `Materialized ${controls.length} risk control(s): ${codes}`,
      });
      handleOpenChange(false);
      onSuccess?.(controls);
    } catch (error) {
      if (error instanceof ConflictError) {
        setConflictVariant(riskControlConflictVariantFromCode(error.code));
        setConflictOpen(true);
      } else if (error instanceof ValidationError) {
        setSubmitError(flattenValidationError(error));
      } else {
        setSubmitError(toUserSafeMessage(error));
      }
    }
  }

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => onOpenChange(true)}>
        Materialize controls
      </Button>

      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          onCloseAutoFocus={(event) => {
            event.preventDefault();
            lastFocusedRef.current?.focus();
          }}
        >
          <DialogHeader
            title="Materialize controls"
            description="Create operational Risk Control records from this assessment's proposed controls."
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 12 }}>
              {isBlocked ? (
                <BlockingReason>
                  Controls can only be materialized from an approved risk
                  assessment.
                </BlockingReason>
              ) : (
                <>
                  {isUnderReview ? (
                    <Checkbox
                      id="materialize-allow-under-review"
                      checked={allowUnderReview}
                      onCheckedChange={(checked) =>
                        setAllowUnderReview(checked === true)
                      }
                      label="Materialize from an assessment still under review"
                    />
                  ) : null}

                  <div style={{ display: "grid", gap: 8 }}>
                    {proposedControls.map((control, index) => {
                      const alreadyMaterialized =
                        control.id !== null &&
                        materializedSourceRefs.has(control.id);
                      const key = control.id ?? `proposed-${index}`;
                      return (
                        <div
                          key={key}
                          style={{
                            display: "grid",
                            gap: 2,
                          }}
                        >
                          <Checkbox
                            id={`materialize-control-${key}`}
                            checked={
                              alreadyMaterialized ||
                              (control.id !== null &&
                                selectedIds.has(control.id))
                            }
                            disabled={
                              alreadyMaterialized || control.id === null
                            }
                            onCheckedChange={(checked) => {
                              if (control.id === null) {
                                return;
                              }
                              toggleSelected(control.id, checked === true);
                            }}
                            label={`${formatRiskControlEnumLabel(control.controlType)} — ${control.description}`}
                          />
                          {alreadyMaterialized ? (
                            <Text variant="caption" tone="muted">
                              Already materialized
                            </Text>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </>
              )}

              <Alert tone="warning" title="Before you continue">
                This creates operational Risk Control records in Draft with no
                owner. Materialization is all-or-nothing — if any selected
                control already exists, nothing is created.
              </Alert>

              {submitError ? (
                <Alert tone="danger" title="Materialization failed">
                  {submitError}
                </Alert>
              ) : null}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={mutation.isPending}
              disabled={!enabled || mutation.isPending}
              onClick={() => void handleConfirm()}
            >
              Materialize
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <RiskControlConflictDialog
        open={conflictOpen}
        onOpenChange={setConflictOpen}
        variant={conflictVariant}
        loading={materializedQuery.isFetching}
        onReload={() => {
          void materializedQuery.refetch();
        }}
      />
    </>
  );
}

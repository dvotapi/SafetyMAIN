"use client";

import { useState } from "react";

import {
  Alert,
  Button,
  ConfirmationDialog,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Label,
  NextActionCard,
  Panel,
  Text,
  TextArea,
} from "@/components";

import { availableLifecycleActions } from "@/features/hazards/hooks/use-hazard-permissions";
import type {
  Hazard,
  HazardCapabilities,
  HazardLifecycleAction,
} from "@/features/hazards/types/hazard-types";

const ACTION_LABELS: Record<HazardLifecycleAction, string> = {
  activate: "Activate hazard",
  archive: "Archive hazard",
  restore: "Restore hazard",
};

export function HazardLifecycleActions({
  hazard,
  capabilities,
  busyAction,
  errorMessage,
  onActivate,
  onArchive,
  onRestore,
}: {
  hazard: Hazard;
  capabilities: HazardCapabilities;
  busyAction?: HazardLifecycleAction | null;
  errorMessage?: string | null;
  onActivate: () => Promise<void> | void;
  onArchive: (reason: string) => Promise<void> | void;
  onRestore: (reason: string) => Promise<void> | void;
}) {
  const actions = availableLifecycleActions(hazard, capabilities);
  const [activateOpen, setActivateOpen] = useState(false);
  const [reasonAction, setReasonAction] = useState<
    "archive" | "restore" | null
  >(null);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);

  if (actions.length === 0) {
    return (
      <Panel>
        <Text tone="secondary">
          No lifecycle actions are available for this hazard in its current
          state.
        </Text>
      </Panel>
    );
  }

  const primary = actions[0];

  return (
    <Panel>
      <NextActionCard
        title="Lifecycle"
        description={`Current status: ${hazard.status}. Choose the next permitted action.`}
        actions={
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {actions.map((action) => (
              <Button
                key={action}
                variant={action === primary ? "primary" : "secondary"}
                size="sm"
                loading={busyAction === action}
                disabled={Boolean(busyAction)}
                onClick={() => {
                  if (action === "activate") {
                    setActivateOpen(true);
                  } else {
                    setReason("");
                    setReasonError(null);
                    setReasonAction(action);
                  }
                }}
              >
                {ACTION_LABELS[action]}
              </Button>
            ))}
          </div>
        }
      />
      {errorMessage ? (
        <Alert tone="danger" title="Lifecycle action failed">
          {errorMessage}
        </Alert>
      ) : null}
      <ConfirmationDialog
        open={activateOpen}
        onOpenChange={setActivateOpen}
        title="Activate hazard"
        description={`Activate this hazard using version ${hazard.version}?`}
        confirmLabel="Activate hazard"
        loading={busyAction === "activate"}
        onConfirm={() => {
          void onActivate();
        }}
      />
      <Dialog
        open={reasonAction !== null}
        onOpenChange={(open) => {
          if (!open) {
            setReasonAction(null);
            setReason("");
            setReasonError(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader
            title={
              reasonAction ? ACTION_LABELS[reasonAction] : "Lifecycle action"
            }
            description={`This action uses version ${hazard.version}.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="lifecycle-reason" required>
                Reason
              </Label>
              <TextArea
                id="lifecycle-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={3}
              />
              {reasonError ? (
                <Alert tone="danger" title="Reason required">
                  {reasonError}
                </Alert>
              ) : null}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => {
                setReasonAction(null);
                setReason("");
                setReasonError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={busyAction === "archive" || busyAction === "restore"}
              onClick={() => {
                if (reason.trim().length === 0) {
                  setReasonError("Reason is required");
                  return;
                }
                const action = reasonAction;
                const value = reason.trim();
                void (async () => {
                  if (action === "archive") {
                    await onArchive(value);
                  } else if (action === "restore") {
                    await onRestore(value);
                  }
                  setReasonAction(null);
                  setReason("");
                  setReasonError(null);
                })();
              }}
            >
              {reasonAction ? ACTION_LABELS[reasonAction] : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Panel>
  );
}

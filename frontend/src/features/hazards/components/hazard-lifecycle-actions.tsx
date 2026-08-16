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
import { hazardStatusLabel } from "@/features/hazards/utils/hazard-status";

const ACTION_LABELS: Record<HazardLifecycleAction, string> = {
  activate: "Активировать опасность",
  archive: "Архивировать опасность",
  restore: "Восстановить опасность",
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
          Для этой опасности в текущем состоянии нет доступных действий
          жизненного цикла.
        </Text>
      </Panel>
    );
  }

  const primary = actions[0];

  return (
    <Panel>
      <NextActionCard
        title="Жизненный цикл"
        description={`Текущий статус: ${hazardStatusLabel(hazard.status)}. Выберите следующее разрешённое действие.`}
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
        <Alert tone="danger" title="Не удалось выполнить действие">
          {errorMessage}
        </Alert>
      ) : null}
      <ConfirmationDialog
        open={activateOpen}
        onOpenChange={setActivateOpen}
        title="Активировать опасность"
        description={`Активировать эту опасность с версией ${hazard.version}?`}
        confirmLabel="Активировать опасность"
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
              reasonAction
                ? ACTION_LABELS[reasonAction]
                : "Действие жизненного цикла"
            }
            description={`Действие использует версию ${hazard.version}.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="lifecycle-reason" required>
                Причина
              </Label>
              <TextArea
                id="lifecycle-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={3}
              />
              {reasonError ? (
                <Alert tone="danger" title="Укажите причину">
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
              Отмена
            </Button>
            <Button
              variant="primary"
              loading={busyAction === "archive" || busyAction === "restore"}
              onClick={() => {
                if (reason.trim().length === 0) {
                  setReasonError("Укажите причину");
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
              {reasonAction ? ACTION_LABELS[reasonAction] : "Подтвердить"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Panel>
  );
}

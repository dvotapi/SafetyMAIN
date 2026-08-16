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
  Select,
  Text,
  TextArea,
} from "@/components";

import { availableLifecycleActions } from "@/features/risk-assessments/hooks/use-risk-assessment-permissions";
import { ACCEPTANCE_DECISIONS } from "@/features/risk-assessments/schemas/risk-assessment-form-schema";
import type {
  AcceptanceDecisionDto,
  RiskAssessment,
  RiskAssessmentCapabilities,
  RiskAssessmentLifecycleAction,
} from "@/features/risk-assessments/types/risk-assessment-types";
import {
  prefillApproveAcceptance,
  toApproveAcceptanceInput,
  validateApproveAcceptance,
  type ApproveAcceptanceInput,
} from "@/features/risk-assessments/utils/approve-acceptance";
import {
  acceptanceDecisionLabel,
  riskAssessmentStatusLabel,
} from "@/features/risk-assessments/utils/risk-assessment-status";

export type { ApproveAcceptanceInput };

const ACTION_LABELS: Record<RiskAssessmentLifecycleAction, string> = {
  submit_for_review: "Отправить на рассмотрение",
  approve: "Утвердить оценку",
  archive: "Архивировать оценку",
};

export function RiskAssessmentLifecycleActions({
  assessment,
  capabilities,
  busyAction,
  errorMessage,
  onSubmitForReview,
  onApprove,
  onArchive,
}: {
  assessment: RiskAssessment;
  capabilities: RiskAssessmentCapabilities;
  busyAction?: RiskAssessmentLifecycleAction | null;
  errorMessage?: string | null;
  onSubmitForReview: () => Promise<boolean> | boolean;
  onApprove: (acceptance: ApproveAcceptanceInput) => Promise<boolean> | boolean;
  onArchive: (reason: string) => Promise<boolean> | boolean;
}) {
  const actions = availableLifecycleActions(assessment, capabilities);
  const [submitOpen, setSubmitOpen] = useState(false);
  const [approveOpen, setApproveOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [archiveReason, setArchiveReason] = useState("");
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const [approveDecision, setApproveDecision] = useState<
    AcceptanceDecisionDto | ""
  >("");
  const [approveJustification, setApproveJustification] = useState("");
  const [approveError, setApproveError] = useState<string | null>(null);

  if (actions.length === 0) {
    return (
      <Panel>
        <Text tone="secondary">
          Для этой оценки риска в текущем состоянии нет доступных действий
          жизненного цикла.
        </Text>
      </Panel>
    );
  }

  const primary = actions[0];

  function openApproveDialog() {
    const prefilled = prefillApproveAcceptance(assessment.acceptance);
    setApproveDecision(prefilled.decision);
    setApproveJustification(prefilled.justification);
    setApproveError(null);
    setApproveOpen(true);
  }

  return (
    <Panel>
      <NextActionCard
        title="Жизненный цикл"
        description={`Текущий статус: ${riskAssessmentStatusLabel(assessment.status)}. Выберите следующее разрешённое действие.`}
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
                  if (action === "submit_for_review") {
                    setSubmitOpen(true);
                  } else if (action === "approve") {
                    openApproveDialog();
                  } else {
                    setArchiveReason("");
                    setArchiveError(null);
                    setArchiveOpen(true);
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
        open={submitOpen}
        onOpenChange={setSubmitOpen}
        title="Отправить на рассмотрение"
        description={`Отправить этот черновик на рассмотрение с версией ${assessment.version}?`}
        confirmLabel="Отправить на рассмотрение"
        loading={busyAction === "submit_for_review"}
        onConfirm={() => {
          void onSubmitForReview();
        }}
      />

      <Dialog open={approveOpen} onOpenChange={setApproveOpen}>
        <DialogContent>
          <DialogHeader
            title="Утвердить оценку"
            description={`Утверждение с версией ${assessment.version}. При утверждении предыдущая оценка в той же области может быть автоматически замещена.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 12 }}>
              <Alert tone="warning" title="Замещение">
                Если в той же области (опасность/профиль/объект) уже есть
                утверждённая оценка, сервер заместит её. Интерфейс не выбирает,
                какая оценка будет замещена.
              </Alert>
              <Text tone="secondary">
                Рецензент может подтвердить или изменить решение о принятии
                перед утверждением. Ниже подставлены значения из оценки, если
                они есть.
              </Text>
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="approve-acceptance" required>
                  Решение о принятии
                </Label>
                <Select
                  id="approve-acceptance"
                  value={approveDecision}
                  onValueChange={(value) =>
                    setApproveDecision(
                      value === "" ? "" : (value as AcceptanceDecisionDto),
                    )
                  }
                  options={[
                    { value: "", label: "Выберите решение" },
                    ...ACCEPTANCE_DECISIONS.map((value) => ({
                      value,
                      label: acceptanceDecisionLabel(value),
                    })),
                  ]}
                />
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="approve-justification">Обоснование</Label>
                <TextArea
                  id="approve-justification"
                  rows={3}
                  value={approveJustification}
                  onChange={(event) =>
                    setApproveJustification(event.target.value)
                  }
                />
              </div>
              {approveError ? (
                <Alert tone="danger" title="Требуется принятие">
                  {approveError}
                </Alert>
              ) : null}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setApproveOpen(false)}>
              Отмена
            </Button>
            <Button
              variant="primary"
              loading={busyAction === "approve"}
              onClick={() => {
                const draft = {
                  decision: approveDecision,
                  justification: approveJustification,
                };
                const validationError = validateApproveAcceptance(draft);
                if (validationError) {
                  setApproveError(validationError);
                  return;
                }
                const payload = toApproveAcceptanceInput(draft);
                if (!payload) {
                  setApproveError("Укажите решение о принятии");
                  return;
                }
                setApproveError(null);
                void (async () => {
                  const succeeded = await onApprove(payload);
                  if (succeeded) {
                    setApproveOpen(false);
                  }
                })();
              }}
            >
              Утвердить оценку
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={archiveOpen}
        onOpenChange={(open) => {
          if (!open) {
            setArchiveOpen(false);
          }
        }}
      >
        <DialogContent>
          <DialogHeader
            title="Архивировать оценку"
            description={`Действие выполняется с версией ${assessment.version}.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="archive-reason" required>
                Причина
              </Label>
              <TextArea
                id="archive-reason"
                value={archiveReason}
                onChange={(event) => setArchiveReason(event.target.value)}
                rows={3}
              />
              {archiveError ? (
                <Alert tone="danger" title="Требуется причина">
                  {archiveError}
                </Alert>
              ) : null}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => {
                setArchiveOpen(false);
                setArchiveReason("");
                setArchiveError(null);
              }}
            >
              Отмена
            </Button>
            <Button
              variant="primary"
              loading={busyAction === "archive"}
              onClick={() => {
                if (archiveReason.trim().length === 0) {
                  setArchiveError("Укажите причину");
                  return;
                }
                const value = archiveReason.trim();
                setArchiveError(null);
                void (async () => {
                  const succeeded = await onArchive(value);
                  if (succeeded) {
                    setArchiveOpen(false);
                    setArchiveReason("");
                    setArchiveError(null);
                  }
                })();
              }}
            >
              Архивировать оценку
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Panel>
  );
}

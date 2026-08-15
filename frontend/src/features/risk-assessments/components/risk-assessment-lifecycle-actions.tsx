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
import { formatRiskAssessmentEnumLabel } from "@/features/risk-assessments/utils/risk-assessment-status";

export type { ApproveAcceptanceInput };

const ACTION_LABELS: Record<RiskAssessmentLifecycleAction, string> = {
  submit_for_review: "Submit for review",
  approve: "Approve assessment",
  archive: "Archive assessment",
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
          No lifecycle actions are available for this risk assessment in its
          current state.
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
        title="Lifecycle"
        description={`Current status: ${formatRiskAssessmentEnumLabel(assessment.status)}. Choose the next permitted action.`}
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
        <Alert tone="danger" title="Lifecycle action failed">
          {errorMessage}
        </Alert>
      ) : null}

      <ConfirmationDialog
        open={submitOpen}
        onOpenChange={setSubmitOpen}
        title="Submit for review"
        description={`Submit this draft for review using version ${assessment.version}?`}
        confirmLabel="Submit for review"
        loading={busyAction === "submit_for_review"}
        onConfirm={() => {
          void onSubmitForReview();
        }}
      />

      <Dialog open={approveOpen} onOpenChange={setApproveOpen}>
        <DialogContent>
          <DialogHeader
            title="Approve assessment"
            description={`Approve using version ${assessment.version}. Approval may automatically supersede a previous approved assessment in the same scope.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 12 }}>
              <Alert tone="warning" title="Superseding">
                If another approved assessment exists for the same
                hazard/profile/object scope, the backend will supersede it. This
                UI does not choose which assessment is superseded.
              </Alert>
              <Text tone="secondary">
                Reviewers can confirm or override the acceptance decision before
                approval. Values below are pre-filled from the assessment when
                available.
              </Text>
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="approve-acceptance" required>
                  Acceptance decision
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
                    { value: "", label: "Select decision" },
                    ...ACCEPTANCE_DECISIONS.map((value) => ({
                      value,
                      label: formatRiskAssessmentEnumLabel(value),
                    })),
                  ]}
                />
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                <Label htmlFor="approve-justification">Justification</Label>
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
                <Alert tone="danger" title="Acceptance required">
                  {approveError}
                </Alert>
              ) : null}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setApproveOpen(false)}>
              Cancel
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
                  setApproveError("Acceptance decision is required");
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
              Approve assessment
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
            title="Archive assessment"
            description={`This action uses version ${assessment.version}.`}
          />
          <DialogBody>
            <div style={{ display: "grid", gap: 8 }}>
              <Label htmlFor="archive-reason" required>
                Reason
              </Label>
              <TextArea
                id="archive-reason"
                value={archiveReason}
                onChange={(event) => setArchiveReason(event.target.value)}
                rows={3}
              />
              {archiveError ? (
                <Alert tone="danger" title="Reason required">
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
              Cancel
            </Button>
            <Button
              variant="primary"
              loading={busyAction === "archive"}
              onClick={() => {
                if (archiveReason.trim().length === 0) {
                  setArchiveError("Reason is required");
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
              Archive assessment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Panel>
  );
}

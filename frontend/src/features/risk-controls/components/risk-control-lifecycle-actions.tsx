"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import {
  Alert,
  Button,
  DatePicker,
  FieldError,
  HelperText,
  Input,
  Label,
  NextActionCard,
  Panel,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import { availableLifecycleActions } from "@/features/risk-controls/hooks/use-risk-control-permissions";
import {
  DEFAULT_REASON_ONLY_FORM_VALUES,
  DEFAULT_SUPERSEDE_FORM_VALUES,
  DEFAULT_SUSPEND_FORM_VALUES,
  reasonOnlyFormSchema,
  supersedeFormSchema,
  suspendFormSchema,
  type ReasonOnlyFormValues,
  type SupersedeFormValues,
  type SuspendFormValues,
} from "@/features/risk-controls/schemas/lifecycle-command-schema";
import type {
  RiskControl,
  RiskControlCapabilities,
  RiskControlLifecycleAction,
} from "@/features/risk-controls/types/risk-control-types";
import { riskControlStatusLabel } from "@/features/risk-controls/utils/risk-control-status";

const ACTION_LABELS: Record<RiskControlLifecycleAction, string> = {
  assign_owner: "Assign owner",
  plan: "Plan implementation",
  start_implementation: "Start implementation",
  update_progress: "Update progress",
  add_evidence: "Add evidence",
  complete_implementation: "Complete implementation",
  verify: "Verify effectiveness",
  schedule_review: "Schedule review",
  complete_review: "Complete review",
  suspend: "Suspend control",
  resume: "Resume control",
  supersede: "Supersede control",
  cancel: "Cancel control",
  archive: "Archive control",
};

/**
 * Header lifecycle card: renders the primary next action plus every other
 * legal action from `availableLifecycleActions`. `plan`, `start_implementation`,
 * `complete_implementation`, `verify`, and `schedule_review` delegate to
 * dialogs the object page already owns (Tasks B3–B8) — this component only
 * opens them. The five terminal commands (`suspend`, `resume`, `supersede`,
 * `cancel`, `archive`) are new in this task and own their dialogs here.
 */
export function RiskControlLifecycleActions({
  control,
  capabilities,
  busyAction = null,
  errorMessage = null,
  onPlan,
  onStartImplementation,
  onCompleteImplementation,
  onVerify,
  onScheduleReview,
  onSuspend,
  onResume,
  onSupersede,
  onCancel,
  onArchive,
}: {
  control: RiskControl;
  capabilities: RiskControlCapabilities;
  busyAction?: RiskControlLifecycleAction | null;
  errorMessage?: string | null;
  onPlan: () => void;
  onStartImplementation: () => void;
  onCompleteImplementation: () => void;
  onVerify: () => void;
  onScheduleReview: () => void;
  onSuspend: (values: SuspendFormValues) => Promise<boolean> | boolean;
  onResume: () => Promise<boolean> | boolean;
  onSupersede: (values: SupersedeFormValues) => Promise<boolean> | boolean;
  onCancel: (values: ReasonOnlyFormValues) => Promise<boolean> | boolean;
  onArchive: (values: ReasonOnlyFormValues) => Promise<boolean> | boolean;
}) {
  const actions = availableLifecycleActions(control, capabilities);

  const [suspendOpen, setSuspendOpen] = useState(false);
  const [resumeOpen, setResumeOpen] = useState(false);
  const [supersedeOpen, setSupersedeOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);

  const suspendForm = useForm<SuspendFormValues>({
    resolver: zodResolver(suspendFormSchema),
    defaultValues: DEFAULT_SUSPEND_FORM_VALUES,
  });
  useEffect(() => {
    if (suspendOpen) {
      suspendForm.reset(DEFAULT_SUSPEND_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suspendOpen]);

  const supersedeForm = useForm<SupersedeFormValues>({
    resolver: zodResolver(supersedeFormSchema),
    defaultValues: DEFAULT_SUPERSEDE_FORM_VALUES,
  });
  useEffect(() => {
    if (supersedeOpen) {
      supersedeForm.reset(DEFAULT_SUPERSEDE_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supersedeOpen]);

  const cancelForm = useForm<ReasonOnlyFormValues>({
    resolver: zodResolver(reasonOnlyFormSchema),
    defaultValues: DEFAULT_REASON_ONLY_FORM_VALUES,
  });
  useEffect(() => {
    if (cancelOpen) {
      cancelForm.reset(DEFAULT_REASON_ONLY_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cancelOpen]);

  const archiveForm = useForm<ReasonOnlyFormValues>({
    resolver: zodResolver(reasonOnlyFormSchema),
    defaultValues: DEFAULT_REASON_ONLY_FORM_VALUES,
  });
  useEffect(() => {
    if (archiveOpen) {
      archiveForm.reset(DEFAULT_REASON_ONLY_FORM_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [archiveOpen]);

  if (actions.length === 0) {
    return (
      <Panel>
        <Text tone="muted">
          No lifecycle actions are available for this control in its current
          state.
        </Text>
      </Panel>
    );
  }

  const primary = actions[0];
  const busy = Boolean(busyAction);

  function handleClick(action: RiskControlLifecycleAction) {
    switch (action) {
      case "plan":
        onPlan();
        break;
      case "start_implementation":
        onStartImplementation();
        break;
      case "complete_implementation":
        onCompleteImplementation();
        break;
      case "verify":
        onVerify();
        break;
      case "schedule_review":
        onScheduleReview();
        break;
      case "suspend":
        setSuspendOpen(true);
        break;
      case "resume":
        setResumeOpen(true);
        break;
      case "supersede":
        setSupersedeOpen(true);
        break;
      case "cancel":
        setCancelOpen(true);
        break;
      case "archive":
        setArchiveOpen(true);
        break;
      default:
        break;
    }
  }

  return (
    <>
      <NextActionCard
        title="Lifecycle"
        description={`Current status: ${riskControlStatusLabel(control.status)}. Choose the next permitted action.`}
        actions={
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {actions.map((action) => (
              <Button
                key={action}
                variant={action === primary ? "primary" : "secondary"}
                size="sm"
                loading={busyAction === action}
                disabled={busy}
                onClick={() => handleClick(action)}
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

      <RiskControlCommandDialog
        open={suspendOpen}
        onOpenChange={setSuspendOpen}
        title="Suspend control"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Suspend control"
        loading={busyAction === "suspend"}
        onConfirm={suspendForm.handleSubmit(async (values) => {
          const succeeded = await onSuspend(values);
          if (succeeded) {
            setSuspendOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="Suspending pauses this control">
            The control stops counting toward active coverage until it is
            resumed. Use this only when the control cannot currently operate as
            intended.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="suspend-reason" required>
              Reason
            </Label>
            <TextArea
              id="suspend-reason"
              {...suspendForm.register("reason")}
              invalid={Boolean(suspendForm.formState.errors.reason)}
            />
            {suspendForm.formState.errors.reason?.message ? (
              <FieldError>
                {suspendForm.formState.errors.reason.message}
              </FieldError>
            ) : null}
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="suspend-expected-resolution-date">
              Expected resolution date
            </Label>
            <DatePicker
              id="suspend-expected-resolution-date"
              {...suspendForm.register("expectedResolutionDate")}
            />
          </div>
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={resumeOpen}
        onOpenChange={setResumeOpen}
        title="Resume control"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Resume control"
        loading={busyAction === "resume"}
        onConfirm={() => {
          void (async () => {
            const succeeded = await onResume();
            if (succeeded) {
              setResumeOpen(false);
            }
          })();
        }}
      >
        <Text tone="secondary">
          Resume this control using version {control.version}? It returns to
          active status.
        </Text>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={supersedeOpen}
        onOpenChange={setSupersedeOpen}
        title="Supersede control"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Supersede control"
        loading={busyAction === "supersede"}
        onConfirm={supersedeForm.handleSubmit(async (values) => {
          const succeeded = await onSupersede(values);
          if (succeeded) {
            setSupersedeOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="This is a consequential action">
            Superseding is not deletion — the control stays readable in its
            history.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="supersede-replacement-control-id" required>
              Replacement control ID
            </Label>
            <Input
              id="supersede-replacement-control-id"
              {...supersedeForm.register("replacementControlId")}
              invalid={Boolean(
                supersedeForm.formState.errors.replacementControlId,
              )}
            />
            <HelperText>
              The backend does not verify that this ID belongs to an existing
              control — double-check it before confirming.
            </HelperText>
            {supersedeForm.formState.errors.replacementControlId?.message ? (
              <FieldError>
                {supersedeForm.formState.errors.replacementControlId.message}
              </FieldError>
            ) : null}
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="supersede-reason" required>
              Reason
            </Label>
            <TextArea
              id="supersede-reason"
              {...supersedeForm.register("reason")}
              invalid={Boolean(supersedeForm.formState.errors.reason)}
            />
            {supersedeForm.formState.errors.reason?.message ? (
              <FieldError>
                {supersedeForm.formState.errors.reason.message}
              </FieldError>
            ) : null}
          </div>
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        title="Cancel control"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Cancel control"
        loading={busyAction === "cancel"}
        onConfirm={cancelForm.handleSubmit(async (values) => {
          const succeeded = await onCancel(values);
          if (succeeded) {
            setCancelOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="cancel-reason" required>
            Reason
          </Label>
          <TextArea
            id="cancel-reason"
            {...cancelForm.register("reason")}
            invalid={Boolean(cancelForm.formState.errors.reason)}
          />
          {cancelForm.formState.errors.reason?.message ? (
            <FieldError>
              {cancelForm.formState.errors.reason.message}
            </FieldError>
          ) : null}
        </div>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={archiveOpen}
        onOpenChange={setArchiveOpen}
        title="Archive control"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Archive control"
        loading={busyAction === "archive"}
        onConfirm={archiveForm.handleSubmit(async (values) => {
          const succeeded = await onArchive(values);
          if (succeeded) {
            setArchiveOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="This is a consequential action">
            Archiving is not deletion. The control remains readable by direct
            link.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="archive-reason" required>
              Reason
            </Label>
            <TextArea
              id="archive-reason"
              {...archiveForm.register("reason")}
              invalid={Boolean(archiveForm.formState.errors.reason)}
            />
            {archiveForm.formState.errors.reason?.message ? (
              <FieldError>
                {archiveForm.formState.errors.reason.message}
              </FieldError>
            ) : null}
          </div>
        </div>
      </RiskControlCommandDialog>
    </>
  );
}

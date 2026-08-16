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
  assign_owner: "Назначить владельца",
  plan: "Спланировать внедрение",
  start_implementation: "Начать внедрение",
  update_progress: "Обновить прогресс",
  add_evidence: "Добавить доказательство",
  complete_implementation: "Завершить внедрение",
  verify: "Подтвердить эффективность",
  schedule_review: "Назначить пересмотр",
  complete_review: "Завершить пересмотр",
  suspend: "Приостановить меру",
  resume: "Возобновить меру",
  supersede: "Заместить меру",
  cancel: "Отменить меру",
  archive: "Архивировать меру",
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
          Для этой меры в текущем состоянии нет доступных действий жизненного
          цикла.
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
        title="Жизненный цикл"
        description={`Текущий статус: ${riskControlStatusLabel(control.status)}. Выберите следующее разрешённое действие.`}
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
        <Alert
          tone="danger"
          title="Не удалось выполнить действие жизненного цикла"
        >
          {errorMessage}
        </Alert>
      ) : null}

      <RiskControlCommandDialog
        open={suspendOpen}
        onOpenChange={setSuspendOpen}
        title="Приостановить меру"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Приостановить меру"
        loading={busyAction === "suspend"}
        onConfirm={suspendForm.handleSubmit(async (values) => {
          const succeeded = await onSuspend(values);
          if (succeeded) {
            setSuspendOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="Приостановка приостанавливает меру">
            Мера не учитывается в активном покрытии до возобновления.
            Используйте только когда мера временно не может работать как
            задумано.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="suspend-reason" required>
              Причина
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
              Ожидаемая дата устранения
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
        title="Возобновить меру"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Возобновить меру"
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
          Возобновить меру (версия {control.version})? Она вернётся в активный
          статус.
        </Text>
      </RiskControlCommandDialog>

      <RiskControlCommandDialog
        open={supersedeOpen}
        onOpenChange={setSupersedeOpen}
        title="Заместить меру"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Заместить меру"
        loading={busyAction === "supersede"}
        onConfirm={supersedeForm.handleSubmit(async (values) => {
          const succeeded = await onSupersede(values);
          if (succeeded) {
            setSupersedeOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="Последствия действия">
            Замещение — не удаление: мера остаётся доступной в истории.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="supersede-replacement-control-id" required>
              ID замещающей меры
            </Label>
            <Input
              id="supersede-replacement-control-id"
              {...supersedeForm.register("replacementControlId")}
              invalid={Boolean(
                supersedeForm.formState.errors.replacementControlId,
              )}
            />
            <HelperText>
              Сервер не проверяет существование меры с этим ID — проверьте перед
              подтверждением.
            </HelperText>
            {supersedeForm.formState.errors.replacementControlId?.message ? (
              <FieldError>
                {supersedeForm.formState.errors.replacementControlId.message}
              </FieldError>
            ) : null}
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="supersede-reason" required>
              Причина
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
        title="Отменить меру"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Отменить меру"
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
            Причина
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
        title="Архивировать меру"
        version={control.version}
        errorMessage={errorMessage}
        confirmLabel="Архивировать меру"
        loading={busyAction === "archive"}
        onConfirm={archiveForm.handleSubmit(async (values) => {
          const succeeded = await onArchive(values);
          if (succeeded) {
            setArchiveOpen(false);
          }
        })}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <Alert tone="warning" title="Последствия действия">
            Архивирование — не удаление. Мера остаётся доступной по прямой
            ссылке.
          </Alert>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="archive-reason" required>
              Причина
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

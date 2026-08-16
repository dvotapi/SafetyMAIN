"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  Button,
  EmptyState,
  FieldError,
  HelperText,
  Input,
  Label,
  Panel,
  Select,
  Text,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  ownerFormSchema,
  type OwnerFormValues,
} from "@/features/risk-controls/schemas/owner-schema";
import type {
  RiskControlCapabilities,
  RiskControlOwner,
} from "@/features/risk-controls/types/risk-control-types";
import {
  OWNER_TYPES,
  TERMINAL_INACTIVE_STATUSES,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";
import { formatDateTime } from "@/utils/format-date";

const DEFAULT_VALUES: OwnerFormValues = {
  ownerType: "user",
  ownerReference: "",
  displayName: "",
  reason: "",
};

const OWNER_TYPE_OPTIONS = OWNER_TYPES.map((value) => ({
  value,
  label: formatRiskControlEnumLabel(value),
}));

export function ControlOwnerSection({
  owner,
  status,
  version,
  capabilities,
  open,
  onOpenChange,
  onAssign,
  loading = false,
  errorMessage = null,
}: {
  owner: RiskControlOwner | null;
  status: string;
  version: number;
  capabilities: RiskControlCapabilities;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAssign: (values: OwnerFormValues) => void | Promise<void>;
  loading?: boolean;
  errorMessage?: string | null;
}) {
  const canAssign =
    capabilities.canAssignOwner && !TERMINAL_INACTIVE_STATUSES.has(status);

  const form = useForm<OwnerFormValues>({
    resolver: zodResolver(ownerFormSchema),
    defaultValues: DEFAULT_VALUES,
  });

  useEffect(() => {
    if (open) {
      form.reset(DEFAULT_VALUES);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = form;

  return (
    <>
      <Panel
        heading={<Text variant="label">Владелец</Text>}
        actions={
          canAssign ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenChange(true)}
            >
              {owner ? "Изменить владельца" : "Назначить владельца"}
            </Button>
          ) : null
        }
      >
        {owner ? (
          <div style={{ display: "grid", gap: 4 }}>
            <Text>{owner.label}</Text>
            <Text variant="caption" tone="muted">
              {formatRiskControlEnumLabel(owner.ownerType)} · Назначен{" "}
              {formatDateTime(owner.assignedAt)}
            </Text>
          </div>
        ) : (
          <EmptyState
            title="Владелец не назначен"
            description="Назначьте владельца — человека, роль или подразделение."
          />
        )}
      </Panel>

      <RiskControlCommandDialog
        open={open}
        onOpenChange={onOpenChange}
        title={owner ? "Изменить владельца" : "Назначить владельца"}
        version={version}
        errorMessage={errorMessage}
        confirmLabel={owner ? "Изменить владельца" : "Назначить владельца"}
        loading={loading}
        onConfirm={handleSubmit((values) => onAssign(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-type" required>
              Тип владельца
            </Label>
            <Controller
              control={control}
              name="ownerType"
              render={({ field }) => (
                <Select
                  id="owner-type"
                  value={field.value}
                  onValueChange={field.onChange}
                  options={OWNER_TYPE_OPTIONS}
                  invalid={Boolean(errors.ownerType)}
                />
              )}
            />
            {errors.ownerType?.message ? (
              <FieldError>{errors.ownerType.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-reference" required>
              Ссылка на владельца
            </Label>
            <Input
              id="owner-reference"
              {...register("ownerReference")}
              invalid={Boolean(errors.ownerReference)}
            />
            <HelperText>
              Справочника сотрудников пока нет — введите ссылку на владельца,
              принятую в вашей организации.
            </HelperText>
            {errors.ownerReference?.message ? (
              <FieldError>{errors.ownerReference.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-display-name" required>
              Отображаемое имя
            </Label>
            <Input
              id="owner-display-name"
              {...register("displayName")}
              invalid={Boolean(errors.displayName)}
            />
            {errors.displayName?.message ? (
              <FieldError>{errors.displayName.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-reason">Причина</Label>
            <TextArea id="owner-reason" {...register("reason")} />
          </div>
        </div>
      </RiskControlCommandDialog>
    </>
  );
}

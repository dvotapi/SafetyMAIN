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
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";

/** `assign_owner` is blocked by the domain once a control is terminal-inactive. */
const OWNER_ASSIGNMENT_BLOCKED_STATUSES = new Set([
  "superseded",
  "archived",
  "cancelled",
]);

const DEFAULT_VALUES: OwnerFormValues = {
  ownerType: "user",
  ownerReference: "",
  displayName: "",
  reason: "",
};

function formatDateTime(value: string | null): string {
  if (!value) {
    return "—";
  }
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

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
    capabilities.canAssignOwner &&
    !OWNER_ASSIGNMENT_BLOCKED_STATUSES.has(status);

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
        heading={<Text variant="label">Owner</Text>}
        actions={
          canAssign ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onOpenChange(true)}
            >
              {owner ? "Change owner" : "Assign owner"}
            </Button>
          ) : null
        }
      >
        {owner ? (
          <div style={{ display: "grid", gap: 4 }}>
            <Text>{owner.label}</Text>
            <Text variant="caption" tone="muted">
              {formatRiskControlEnumLabel(owner.ownerType)} · Assigned{" "}
              {formatDateTime(owner.assignedAt)}
            </Text>
          </div>
        ) : (
          <EmptyState
            title="No owner assigned"
            description="Assign an owner to make this control accountable to a person, role, or unit."
          />
        )}
      </Panel>

      <RiskControlCommandDialog
        open={open}
        onOpenChange={onOpenChange}
        title={owner ? "Change owner" : "Assign owner"}
        version={version}
        errorMessage={errorMessage}
        confirmLabel={owner ? "Change owner" : "Assign owner"}
        loading={loading}
        onConfirm={handleSubmit((values) => onAssign(values))}
      >
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-type" required>
              Owner type
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
              Owner reference
            </Label>
            <Input
              id="owner-reference"
              {...register("ownerReference")}
              invalid={Boolean(errors.ownerReference)}
            />
            <HelperText>
              No employee directory exists yet — enter the owner reference
              used by your organization.
            </HelperText>
            {errors.ownerReference?.message ? (
              <FieldError>{errors.ownerReference.message}</FieldError>
            ) : null}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Label htmlFor="owner-display-name" required>
              Display name
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
            <Label htmlFor="owner-reason">Reason</Label>
            <TextArea id="owner-reason" {...register("reason")} />
          </div>
        </div>
      </RiskControlCommandDialog>
    </>
  );
}

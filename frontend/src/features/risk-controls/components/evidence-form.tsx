"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  Alert,
  Checkbox,
  FieldError,
  Input,
  Label,
  Select,
  TextArea,
} from "@/components";
import { RiskControlCommandDialog } from "@/features/risk-controls/components/risk-control-command-dialog";
import {
  DEFAULT_EVIDENCE_FORM_VALUES,
  buildEvidenceFormSchema,
  type EvidenceFormValues,
} from "@/features/risk-controls/schemas/evidence-schema";
import {
  EVIDENCE_TYPES,
  formatRiskControlEnumLabel,
} from "@/features/risk-controls/utils/risk-control-status";

/** Statuses where a control has already been marked implemented — adding
 * evidence here is a deliberate append to the record, gated behind an
 * explicit acknowledgement checkbox rather than a silent flag. */
const POST_IMPLEMENTATION_STATUSES = new Set([
  "implemented",
  "verified_effective",
  "verified_ineffective",
]);

const EVIDENCE_TYPE_OPTIONS = EVIDENCE_TYPES.map((value) => ({
  value,
  label: formatRiskControlEnumLabel(value),
}));

/**
 * Add-evidence form. Evidence is a reference (external system, document ID,
 * checksum, ...), never a file — this component intentionally has no
 * `<input type="file">` and no binary upload affordance anywhere in it.
 */
export function EvidenceForm({
  status,
  version,
  open,
  onOpenChange,
  onSubmit,
  loading = false,
  errorMessage = null,
}: {
  status: string;
  version: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: EvidenceFormValues) => void | Promise<void>;
  loading?: boolean;
  errorMessage?: string | null;
}) {
  const isPostImplementation = POST_IMPLEMENTATION_STATUSES.has(status);

  const schema = useMemo(
    () => buildEvidenceFormSchema(isPostImplementation),
    [isPostImplementation],
  );

  const form = useForm<EvidenceFormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULT_EVIDENCE_FORM_VALUES,
  });

  useEffect(() => {
    if (open) {
      form.reset(DEFAULT_EVIDENCE_FORM_VALUES);
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
    <RiskControlCommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Добавить доказательство"
      version={version}
      errorMessage={errorMessage}
      confirmLabel="Добавить доказательство"
      loading={loading}
      onConfirm={handleSubmit((values) => onSubmit(values))}
    >
      <div style={{ display: "grid", gap: 12 }}>
        {isPostImplementation ? (
          <Alert tone="warning">
            Мера уже внедрена. Добавление доказательства сейчас — явное
            дополнение записи.
          </Alert>
        ) : null}

        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="evidence-type" required>
            Тип доказательства
          </Label>
          <Controller
            control={control}
            name="evidenceType"
            render={({ field }) => (
              <Select
                id="evidence-type"
                value={field.value}
                onValueChange={field.onChange}
                options={EVIDENCE_TYPE_OPTIONS}
                invalid={Boolean(errors.evidenceType)}
              />
            )}
          />
          {errors.evidenceType?.message ? (
            <FieldError>{errors.evidenceType.message}</FieldError>
          ) : null}
        </div>

        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="evidence-external-reference" required>
            Внешняя ссылка
          </Label>
          <Input
            id="evidence-external-reference"
            {...register("externalReference")}
            invalid={Boolean(errors.externalReference)}
          />
          {errors.externalReference?.message ? (
            <FieldError>{errors.externalReference.message}</FieldError>
          ) : null}
        </div>

        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="evidence-title" required>
            Название
          </Label>
          <Input
            id="evidence-title"
            {...register("title")}
            invalid={Boolean(errors.title)}
          />
          {errors.title?.message ? (
            <FieldError>{errors.title.message}</FieldError>
          ) : null}
        </div>

        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="evidence-description">Описание</Label>
          <TextArea id="evidence-description" {...register("description")} />
        </div>

        <div style={{ display: "grid", gap: 8 }}>
          <Label htmlFor="evidence-checksum">Контрольная сумма</Label>
          <Input id="evidence-checksum" {...register("checksum")} />
        </div>

        {isPostImplementation ? (
          <div style={{ display: "grid", gap: 8 }}>
            <Controller
              control={control}
              name="allowAfterImplemented"
              render={({ field }) => (
                <Checkbox
                  id="evidence-allow-after-implemented"
                  checked={field.value}
                  onCheckedChange={(checked) =>
                    field.onChange(checked === true)
                  }
                  label="Добавить доказательство после внедрения"
                />
              )}
            />
            {errors.allowAfterImplemented?.message ? (
              <FieldError>{errors.allowAfterImplemented.message}</FieldError>
            ) : null}
          </div>
        ) : null}
      </div>
    </RiskControlCommandDialog>
  );
}

"use client";

import { Controller, type UseFormReturn } from "react-hook-form";

import {
  FieldError,
  Form,
  FormRow,
  FormSection,
  Input,
  Label,
  MultiSelect,
  Select,
  TextArea,
  ValidationSummary,
} from "@/components";
import {
  AFFECTED_SUBJECTS,
  HAZARD_CATEGORIES,
  HAZARD_SOURCES,
  SAFETY_DIRECTIONS,
  type HazardFormValues,
} from "@/features/hazards/schemas/hazard-form-schema";
import {
  affectedSubjectLabel,
  hazardCategoryLabel,
  hazardSourceLabel,
  safetyDirectionLabel,
} from "@/features/hazards/utils/hazard-status";

function categoryOptions() {
  return HAZARD_CATEGORIES.map((value) => ({
    value,
    label: hazardCategoryLabel(value),
  }));
}

function directionOptions() {
  return SAFETY_DIRECTIONS.map((value) => ({
    value,
    label: safetyDirectionLabel(value),
  }));
}

function sourceOptions() {
  return HAZARD_SOURCES.map((value) => ({
    value,
    label: hazardSourceLabel(value),
  }));
}

function subjectOptions() {
  return AFFECTED_SUBJECTS.map((value) => ({
    value,
    label: affectedSubjectLabel(value),
  }));
}

export function HazardForm({
  form,
  onSubmit,
  id = "hazard-form",
  readOnly = false,
  showCode = true,
  sourceEditable = true,
}: {
  form: UseFormReturn<HazardFormValues>;
  onSubmit: (values: HazardFormValues) => void;
  id?: string;
  readOnly?: boolean;
  showCode?: boolean;
  sourceEditable?: boolean;
}) {
  const {
    register,
    control,
    formState: { errors },
  } = form;
  const summaryErrors = Object.values(errors)
    .map((error) => error?.message)
    .filter((message): message is string => Boolean(message));

  return (
    <Form form={form} onSubmit={onSubmit} id={id}>
      {summaryErrors.length > 0 ? (
        <ValidationSummary errors={summaryErrors} />
      ) : null}
      <FormSection title="Сведения об опасности">
        {showCode ? (
          <FormRow>
            <Label htmlFor="hazard-code" required>
              Код
            </Label>
            <Input
              id="hazard-code"
              {...register("code")}
              disabled={readOnly || !showCode}
              invalid={Boolean(errors.code)}
              autoComplete="off"
            />
            {errors.code?.message ? (
              <FieldError>{errors.code.message}</FieldError>
            ) : null}
          </FormRow>
        ) : null}
        <FormRow>
          <Label htmlFor="hazard-title" required>
            Название
          </Label>
          <Input
            id="hazard-title"
            {...register("title")}
            disabled={readOnly}
            invalid={Boolean(errors.title)}
          />
          {errors.title?.message ? (
            <FieldError>{errors.title.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-description">Описание</Label>
          <TextArea
            id="hazard-description"
            rows={4}
            {...register("description")}
            disabled={readOnly}
          />
        </FormRow>
      </FormSection>
      <FormSection title="Классификация">
        <FormRow>
          <Label htmlFor="hazard-category" required>
            Категория
          </Label>
          <Controller
            control={control}
            name="category"
            render={({ field }) => (
              <Select
                id="hazard-category"
                value={field.value}
                onValueChange={field.onChange}
                options={categoryOptions()}
                disabled={readOnly}
                invalid={Boolean(errors.category)}
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-directions" required>
            Направления безопасности
          </Label>
          <Controller
            control={control}
            name="safetyDirections"
            render={({ field }) => (
              <MultiSelect
                id="hazard-directions"
                values={field.value}
                onValuesChange={field.onChange}
                options={directionOptions()}
                disabled={readOnly}
                invalid={Boolean(errors.safetyDirections)}
              />
            )}
          />
          {errors.safetyDirections?.message ? (
            <FieldError>{errors.safetyDirections.message}</FieldError>
          ) : null}
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-source" required>
            Источник
          </Label>
          <Controller
            control={control}
            name="source"
            render={({ field }) => (
              <Select
                id="hazard-source"
                value={field.value}
                onValueChange={field.onChange}
                options={sourceOptions()}
                disabled={readOnly || !sourceEditable}
                invalid={Boolean(errors.source)}
              />
            )}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-subjects">Затронутые объекты</Label>
          <Controller
            control={control}
            name="affectedSubjects"
            render={({ field }) => (
              <MultiSelect
                id="hazard-subjects"
                values={field.value}
                onValuesChange={field.onChange}
                options={subjectOptions()}
                disabled={readOnly}
              />
            )}
          />
        </FormRow>
      </FormSection>
      <FormSection title="Место и область">
        <FormRow>
          <Label htmlFor="hazard-location">Место</Label>
          <Input
            id="hazard-location"
            {...register("locationReference")}
            disabled={readOnly}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-process">Процесс</Label>
          <Input
            id="hazard-process"
            {...register("processReference")}
            disabled={readOnly}
          />
        </FormRow>
        <FormRow>
          <Label htmlFor="hazard-equipment">Оборудование</Label>
          <Input
            id="hazard-equipment"
            {...register("equipmentReference")}
            disabled={readOnly}
          />
        </FormRow>
      </FormSection>
    </Form>
  );
}

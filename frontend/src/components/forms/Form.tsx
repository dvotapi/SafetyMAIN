"use client";

import { type ReactNode } from "react";
import {
  FormProvider,
  type FieldValues,
  type SubmitHandler,
  type UseFormReturn,
} from "react-hook-form";

import { cx } from "@/utils/cx";

export {
  Controller,
  FormProvider,
  useFormContext,
  useFormState,
} from "react-hook-form";

export interface FormProps<TFieldValues extends FieldValues> {
  form: UseFormReturn<TFieldValues>;
  onSubmit: SubmitHandler<TFieldValues>;
  children: ReactNode;
  className?: string;
  id?: string;
}

/** RHF adapter — optional; features supply schema/resolver. */
export function Form<TFieldValues extends FieldValues>({
  form,
  onSubmit,
  children,
  className,
  id,
}: FormProps<TFieldValues>) {
  return (
    <FormProvider {...form}>
      <form
        id={id}
        className={cx(className)}
        noValidate
        onSubmit={form.handleSubmit(onSubmit)}
      >
        {children}
      </form>
    </FormProvider>
  );
}

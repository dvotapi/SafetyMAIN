"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/primitives/Button";
import { Text } from "@/components/primitives/Text";

const demoSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters"),
});

type DemoValues = z.infer<typeof demoSchema>;

/** Minimal RHF + Zod adapter proof — not a business form. */
export function DemoValidatedForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DemoValues>({
    resolver: zodResolver(demoSchema),
    defaultValues: { title: "" },
  });

  return (
    <form
      onSubmit={handleSubmit(() => undefined)}
      noValidate
      style={{ display: "grid", gap: "var(--sm-space-3)", maxWidth: 420 }}
    >
      <label>
        <Text as="span" variant="label">
          Title
        </Text>
        <input
          aria-invalid={Boolean(errors.title)}
          aria-describedby={errors.title ? "title-error" : undefined}
          {...register("title")}
        />
      </label>
      {errors.title ? (
        <Text id="title-error" tone="muted" variant="caption" role="alert">
          {errors.title.message}
        </Text>
      ) : null}
      <Button type="submit">Validate</Button>
    </form>
  );
}

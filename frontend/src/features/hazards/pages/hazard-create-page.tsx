"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { Alert, Button, EmptyState, useToast } from "@/components";
import {
  PageActions,
  PageContainer,
  PageHeader,
} from "@/components/patterns/Page";
import { useCreateHazardMutation } from "@/features/hazards/api/hazard-mutations";
import { HazardForm } from "@/features/hazards/components/hazard-form";
import { mapHazardCapabilities } from "@/features/hazards/hooks/use-hazard-permissions";
import { formValuesToCreateRequest } from "@/features/hazards/mappers/hazard-mappers";
import {
  defaultHazardFormValues,
  hazardFormSchema,
  type HazardFormValues,
} from "@/features/hazards/schemas/hazard-form-schema";
import { useAuth } from "@/hooks/auth";
import {
  ConflictError,
  PermissionError,
  ValidationError,
  toUserSafeMessage,
} from "@/services/api/errors";

export function HazardCreatePage() {
  const { hasPermission } = useAuth();
  const capabilities = mapHazardCapabilities(hasPermission);
  const router = useRouter();
  const { toast } = useToast();
  const mutation = useCreateHazardMutation();
  const form = useForm<HazardFormValues>({
    resolver: zodResolver(hazardFormSchema),
    defaultValues: defaultHazardFormValues,
    mode: "onSubmit",
  });

  useEffect(() => {
    document.title = "Создать опасность · SafetyMAIN";
  }, []);

  if (!capabilities.canCreate) {
    return (
      <PageContainer>
        <EmptyState
          title="Нельзя создать опасности"
          description="Недостаточно прав для создания опасностей."
          action={<Link href="/safety/hazards">К реестру</Link>}
        />
      </PageContainer>
    );
  }

  async function onSubmit(values: HazardFormValues) {
    try {
      const hazard = await mutation.mutateAsync(
        formValuesToCreateRequest(values),
      );
      toast({
        tone: "success",
        title: "Опасность создана",
        description: hazard.code,
      });
      router.push(`/safety/hazards/${hazard.id}`);
    } catch (error) {
      if (error instanceof ValidationError) {
        form.setError("root", { message: error.message });
        const firstInvalid = Object.keys(form.formState.errors)[0];
        if (firstInvalid) {
          form.setFocus(firstInvalid as keyof HazardFormValues);
        }
        return;
      }
      if (error instanceof ConflictError) {
        form.setError("code", {
          message: error.message || "Опасность с таким кодом уже существует.",
        });
        return;
      }
      if (error instanceof PermissionError) {
        form.setError("root", { message: toUserSafeMessage(error) });
        return;
      }
      form.setError("root", { message: toUserSafeMessage(error) });
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Создать опасность"
        description="Зафиксируйте сведения об идентификации. Новые опасности создаются в статусе «Черновик»."
        actions={
          <PageActions>
            <Button asChild variant="secondary">
              <Link href="/safety/hazards">Отмена</Link>
            </Button>
            <Button
              type="submit"
              form="hazard-create-form"
              loading={mutation.isPending}
              disabled={mutation.isPending}
            >
              Создать опасность
            </Button>
          </PageActions>
        }
      />
      {form.formState.errors.root?.message ? (
        <Alert tone="danger" title="Не удалось создать опасность">
          {form.formState.errors.root.message}
        </Alert>
      ) : null}
      <HazardForm
        id="hazard-create-form"
        form={form}
        onSubmit={onSubmit}
        showCode
        sourceEditable
      />
    </PageContainer>
  );
}

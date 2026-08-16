"use client";

import { useEffect, useRef } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components";

export type RiskControlConflictVariant =
  "version_conflict" | "duplicate_materialization";

/** Backend error codes that select the duplicate-materialization copy. */
const DUPLICATE_MATERIALIZATION_CODE = "risk_control_already_materialized";

/**
 * Chooses the conflict dialog variant from the API error code, never from
 * HTTP status alone (both variants surface as 409 Conflict).
 */
export function riskControlConflictVariantFromCode(
  code?: string,
): RiskControlConflictVariant {
  return code === DUPLICATE_MATERIALIZATION_CODE
    ? "duplicate_materialization"
    : "version_conflict";
}

const VARIANT_COPY: Record<
  RiskControlConflictVariant,
  { title: string; description: string; alertTitle: string }
> = {
  version_conflict: {
    title: "Мера изменена в другом месте",
    description:
      "Другой пользователь обновил эту меру. Ваши изменения не сохранены.",
    alertTitle: "Конфликт версий",
  },
  duplicate_materialization: {
    title: "Меры уже созданы",
    description:
      "Для одной или нескольких предложенных мер уже существует запись. Создание выполняется целиком — ничего не создано. Обновите список, чтобы увидеть текущие меры.",
    alertTitle: "Уже создано",
  },
};

export function RiskControlConflictDialog({
  open,
  onOpenChange,
  onReload,
  loading,
  variant = "version_conflict",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReload: () => void;
  loading?: boolean;
  variant?: RiskControlConflictVariant;
}) {
  const copy = VARIANT_COPY[variant];
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      lastFocusedRef.current = document.activeElement as HTMLElement | null;
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          lastFocusedRef.current?.focus();
        }}
      >
        <DialogHeader title={copy.title} description={copy.description} />
        <DialogBody>
          <Alert tone="warning" title={copy.alertTitle}>
            Обновите последнюю версию и повторите действие. Повторная отправка
            не выполняется автоматически.
          </Alert>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Оставить черновик
          </Button>
          <Button
            variant="primary"
            {...(loading ? { loading: true } : {})}
            onClick={() => {
              onReload();
              onOpenChange(false);
            }}
          >
            Обновить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

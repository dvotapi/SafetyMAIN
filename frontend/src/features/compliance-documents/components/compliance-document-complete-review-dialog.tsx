"use client";

import { useEffect, useRef, useState } from "react";

import {
  Alert,
  Button,
  DatePicker,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Label,
} from "@/components";

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function CompleteReviewDialog({
  open,
  onOpenChange,
  loading,
  errorMessage,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  loading: boolean;
  errorMessage?: string | null;
  onConfirm: (payload: {
    completed_on: string;
    next_review_at?: string | null;
  }) => void;
}) {
  const [completedOn, setCompletedOn] = useState("");
  const [nextReviewAt, setNextReviewAt] = useState("");
  const lastFocusedRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      lastFocusedRef.current = document.activeElement as HTMLElement | null;
      setCompletedOn(toIsoDate(new Date()));
      setNextReviewAt("");
    }
  }, [open]);

  const canConfirm = completedOn !== "" && !loading;

  function handleConfirm() {
    onConfirm({
      completed_on: completedOn,
      next_review_at: nextReviewAt === "" ? null : nextReviewAt,
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          lastFocusedRef.current?.focus();
        }}
      >
        <DialogHeader
          title="Завершить пересмотр"
          description="Укажите дату завершения пересмотра. Следующий пересмотр можно оставить пустым — тип документа задаст его автоматически."
        />
        <DialogBody>
          <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
            <div style={{ display: "grid", gap: "var(--sm-space-2)" }}>
              <Label htmlFor="compliance-document-completed-on">
                Дата завершения
              </Label>
              <DatePicker
                id="compliance-document-completed-on"
                value={completedOn}
                onChange={(e) => setCompletedOn(e.target.value)}
              />
            </div>
            <div style={{ display: "grid", gap: "var(--sm-space-2)" }}>
              <Label htmlFor="compliance-document-next-review-at">
                Следующий пересмотр (опционально)
              </Label>
              <DatePicker
                id="compliance-document-next-review-at"
                value={nextReviewAt}
                onChange={(e) => setNextReviewAt(e.target.value)}
              />
            </div>
            {errorMessage ? (
              <Alert tone="danger" title="Не удалось завершить пересмотр">
                {errorMessage}
              </Alert>
            ) : null}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button
            variant="primary"
            loading={loading}
            disabled={!canConfirm}
            onClick={handleConfirm}
          >
            Завершить пересмотр
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

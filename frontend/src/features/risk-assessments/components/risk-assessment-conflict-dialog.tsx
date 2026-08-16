"use client";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
} from "@/components";

export function RiskAssessmentConflictDialog({
  open,
  onOpenChange,
  onReload,
  loading,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReload: () => void;
  loading?: boolean;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader
          title="Оценка риска изменена в другом месте"
          description="Другой пользователь обновил эту оценку. Ваши изменения не сохранены."
        />
        <DialogBody>
          <Alert tone="warning" title="Конфликт версий">
            Загрузите последнюю версию и повторите правки. Повтор не выполняется
            автоматически.
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
            Загрузить последнюю версию
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

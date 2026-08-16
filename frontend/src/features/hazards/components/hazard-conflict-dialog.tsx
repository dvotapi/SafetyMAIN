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

export function HazardConflictDialog({
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
          title="Опасность изменена в другом месте"
          description="Другой пользователь обновил эту опасность. Ваши изменения не сохранены."
        />
        <DialogBody>
          <Alert tone="warning" title="Конфликт версий">
            Загрузите актуальную версию, затем внесите правки снова. Повтор
            мутации автоматически не выполняется.
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
            Загрузить актуальную
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

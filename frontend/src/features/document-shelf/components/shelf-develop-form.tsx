"use client";

import { useId, useState } from "react";

import { Alert, Button, Label, Select, Text } from "@/components";

import { useActiveDocumentTypesQuery } from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";

/** Asked only when the place names no document type (§4.3.8). */
export function ShelfDevelopForm({
  proposedType,
  submitting,
  error,
  onSubmit,
  onCancel,
}: {
  proposedType: string;
  submitting: boolean;
  error: string | null;
  onSubmit: (documentTypeCode: string) => void;
  onCancel: () => void;
}) {
  const id = useId();
  const types = useActiveDocumentTypesQuery(true);
  const [code, setCode] = useState("");
  return (
    <form
      className={styles.panelBlock}
      aria-labelledby={`${id}-title`}
      onSubmit={(event) => {
        event.preventDefault();
        if (code) onSubmit(code);
      }}
    >
      <h3 id={`${id}-title`} className={styles.panelHeading}>
        Тип документа
      </h3>
      <Text as="p" tone="muted">
        У места не указан тип документа. Выберите его, чтобы создать проект.
        {proposedType ? ` В реестре предложено: «${proposedType}».` : ""}
      </Text>
      <div className={styles.field}>
        <Label htmlFor={`${id}-type`} required>
          Тип
        </Label>
        <Select
          id={`${id}-type`}
          value={code}
          onValueChange={setCode}
          disabled={types.isPending}
          options={(types.data ?? []).map((item) => ({
            value: item.code,
            label: item.title_ru,
          }))}
        />
      </div>
      {error ? (
        <Alert tone="danger" title="Не удалось создать проект">
          {error}
        </Alert>
      ) : null}
      <div className={styles.controls}>
        <Button
          type="submit"
          disabled={!code || submitting}
          loading={submitting}
        >
          Создать проект
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Отмена
        </Button>
      </div>
    </form>
  );
}

"use client";

import { useEffect, useId, useState } from "react";

import { Alert, Button, Input, Label, Text } from "@/components";

import { useDocumentSearchQuery } from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import { DOCUMENT_STATUS_LABELS } from "@/features/document-shelf/utils/shelf-labels";

/** Find an organization document by code or title and link it (plan P17). */
export function ShelfLinkPicker({
  submitting,
  error,
  onPick,
  onCancel,
}: {
  submitting: boolean;
  error: string | null;
  onPick: (documentId: string) => void;
  onCancel: () => void;
}) {
  const id = useId();
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  useEffect(() => {
    const handle = window.setTimeout(() => setSearch(draft), 250);
    return () => window.clearTimeout(handle);
  }, [draft]);
  const results = useDocumentSearchQuery(search);

  return (
    <section className={styles.panelBlock} aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className={styles.panelHeading}>
        Привязать документ
      </h3>
      <div className={styles.field}>
        <Label htmlFor={`${id}-search`}>Код или название</Label>
        <Input
          id={`${id}-search`}
          value={draft}
          autoComplete="off"
          onChange={(event) => setDraft(event.target.value)}
        />
      </div>
      {search.trim().length >= 2 ? (
        results.isPending ? (
          <Text tone="muted">Поиск…</Text>
        ) : results.data && results.data.length > 0 ? (
          <ul className={styles.pickList} aria-label="Найденные документы">
            {results.data.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={styles.pickItem}
                  disabled={submitting}
                  onClick={() => onPick(item.id)}
                >
                  <span className={styles.mono}>{item.code}</span> {item.title}
                  <span className={styles.ink}>
                    {" · "}
                    {DOCUMENT_STATUS_LABELS[item.status] ?? item.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <Text tone="muted">Ничего не найдено.</Text>
        )
      ) : null}
      {error ? (
        <Alert tone="danger" title="Не удалось привязать">
          {error}
        </Alert>
      ) : null}
      <div className={styles.controls}>
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Отмена
        </Button>
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import {
  Alert,
  Button,
  IconButton,
  Skeleton,
  Text,
  TextButton,
} from "@/components";
import { ComplianceDocumentUploadDialog } from "@/features/compliance-documents";

import {
  useConfirmShelfSlotApplicableMutation,
  useDevelopShelfSlotMutation,
  useExcludeShelfSlotMutation,
  useLinkShelfSlotDocumentMutation,
  useRefreshShelf,
  useRestoreShelfSlotMutation,
} from "@/features/document-shelf/api/shelf-mutations";
import {
  useShelfDocumentQuery,
  useShelfSlotQuery,
} from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import { ShelfDevelopForm } from "@/features/document-shelf/components/shelf-develop-form";
import { ShelfExclusionForm } from "@/features/document-shelf/components/shelf-exclusion-form";
import { ShelfLinkPicker } from "@/features/document-shelf/components/shelf-link-picker";
import { ShelfScanBlock } from "@/features/document-shelf/components/shelf-scan-block";
import { ShelfStatusBadge } from "@/features/document-shelf/components/shelf-status-badge";
import type {
  ShelfAction,
  ShelfSlotDetailDto,
} from "@/features/document-shelf/types/shelf-dto";
import {
  ACTION_LABELS,
  EXCLUSION_REASON_LABELS,
} from "@/features/document-shelf/utils/shelf-actions";
import { shelfErrorMessage } from "@/features/document-shelf/utils/shelf-errors";
import {
  DOCUMENT_STATUS_LABELS,
  OBLIGATION_LABELS,
} from "@/features/document-shelf/utils/shelf-labels";
import { formatDateOnly, formatDateTime } from "@/utils/format-date";

type Mode =
  | { kind: "view" }
  | { kind: "exclude" }
  | { kind: "develop"; then: "edit" | "upload" }
  | { kind: "link" }
  | { kind: "upload"; documentId: string; target: "working" | "signed_scan" };

const EMPTY_STATES: Partial<
  Record<ShelfSlotDetailDto["effective_status"], string>
> = {
  missing: "Место есть, документа нет",
  to_clarify: "Нужно уточнить применимость",
  in_progress: "Проект в работе",
  present_unverified: "Отмечено как есть, но документа в системе нет",
};

function projectDocumentId(slot: ShelfSlotDetailDto): string | null {
  return (
    slot.editions.find(
      (item) => item.status === "draft" || item.status === "approved",
    )?.id ?? null
  );
}

export function ShelfPlacePanel({
  slotId,
  onClose,
  onExcluded,
}: {
  slotId: string;
  onClose: () => void;
  onExcluded: (codes: string[], slotIds: string[]) => void;
}) {
  const router = useRouter();
  const query = useShelfSlotQuery(slotId);
  const [mode, setMode] = useState<Mode>({ kind: "view" });
  const [error, setError] = useState<string | null>(null);
  const exclude = useExcludeShelfSlotMutation();
  const restore = useRestoreShelfSlotMutation();
  const confirm = useConfirmShelfSlotApplicableMutation();
  const develop = useDevelopShelfSlotMutation();
  const link = useLinkShelfSlotDocumentMutation();
  const uploadTarget = mode.kind === "upload" ? mode.documentId : null;
  const uploadDocument = useShelfDocumentQuery(uploadTarget);
  const refreshShelf = useRefreshShelf();
  const panelRef = useRef<HTMLElement>(null);
  const lastTrigger = useRef<string | null>(null);
  const busy =
    develop.isPending ||
    confirm.isPending ||
    restore.isPending ||
    link.isPending;

  // Forms focus their own heading; on return, focus goes back to the trigger (WCAG 2.4.3).
  useEffect(() => {
    if (mode.kind !== "view" || !lastTrigger.current) return;
    panelRef.current
      ?.querySelector<HTMLElement>(`[data-action="${lastTrigger.current}"]`)
      ?.focus();
    lastTrigger.current = null;
  }, [mode.kind]);

  if (query.isPending) {
    return (
      <aside
        className={styles.panel}
        aria-label="Место на полке"
        aria-busy="true"
      >
        <Skeleton height="28px" />
        <Skeleton height="220px" />
      </aside>
    );
  }
  if (query.isError) {
    return (
      <aside className={styles.panel} aria-label="Место на полке">
        <Alert tone="danger" title="Не удалось загрузить место">
          {shelfErrorMessage(query.error)}{" "}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void query.refetch()}
          >
            Повторить
          </Button>
        </Alert>
      </aside>
    );
  }

  const slot = query.data;
  const current = slot.current_document;
  const run = async (task: () => Promise<unknown>) => {
    setError(null);
    try {
      await task();
      return true;
    } catch (cause) {
      setError(shelfErrorMessage(cause));
      return false;
    }
  };

  const startDevelop = async (
    then: "edit" | "upload",
    documentTypeCode?: string,
  ) => {
    if (!slot.document_type_code && !documentTypeCode) {
      setMode({ kind: "develop", then });
      return;
    }
    await run(async () => {
      const result = await develop.mutateAsync({
        slotId: slot.id,
        version: slot.version,
        ...(documentTypeCode ? { documentTypeCode } : {}),
      });
      if (then === "edit") {
        router.push(`/compliance-documents/${result.document_id}/edit`);
      } else {
        setMode({
          kind: "upload",
          documentId: result.document_id,
          target: "working",
        });
      }
    });
  };

  const handle = (action: ShelfAction) => {
    lastTrigger.current = action;
    switch (action) {
      case "develop_document":
        void startDevelop("edit");
        return;
      case "upload_scan":
        void startDevelop("upload");
        return;
      case "upload_signed_scan":
        if (current)
          setMode({
            kind: "upload",
            documentId: current.id,
            target: "signed_scan",
          });
        return;
      case "confirm_applicable":
        void run(() =>
          confirm.mutateAsync({ slotId: slot.id, version: slot.version }),
        );
        return;
      case "restore":
        void run(() =>
          restore.mutateAsync({ slotId: slot.id, version: slot.version }),
        );
        return;
      case "exclude":
        setMode({ kind: "exclude" });
        return;
      case "link_document":
        setMode({ kind: "link" });
        return;
      default:
        return;
    }
  };

  const linkFor = (action: ShelfAction): string | null => {
    if (action === "open_document" || action === "start_review") {
      return current ? `/compliance-documents/${current.id}` : null;
    }
    if (action === "open_project") {
      const id = projectDocumentId(slot);
      return id ? `/compliance-documents/${id}` : null;
    }
    return null;
  };

  const renderAction = (action: ShelfAction, primary: boolean) => {
    const href = linkFor(action);
    const label = ACTION_LABELS[action];
    if (href) {
      return (
        <Link
          key={action}
          href={href}
          data-action={action}
          className={primary ? styles.primaryLink : styles.secondaryLink}
        >
          {label}
        </Link>
      );
    }
    if (action === "exclude") {
      return (
        <TextButton
          key={action}
          tone="danger"
          data-action={action}
          disabled={busy}
          onClick={() => handle(action)}
        >
          {label}
        </TextButton>
      );
    }
    if (action === "send_for_acknowledgement") return null;
    return (
      <Button
        key={action}
        variant={primary ? "primary" : "secondary"}
        size="sm"
        data-action={action}
        loading={primary && busy}
        disabled={busy}
        onClick={() => handle(action)}
      >
        {label}
      </Button>
    );
  };

  const subline = [
    slot.subsection_code,
    slot.document_kind,
    OBLIGATION_LABELS[slot.obligation_level] ?? slot.obligation_level,
  ].join(" · ");
  const others = slot.available_actions.filter(
    (action) => action !== slot.primary_action,
  );

  return (
    <aside
      ref={panelRef}
      className={styles.panel}
      aria-labelledby="shelf-panel-title"
    >
      <div className={styles.panelTop}>
        <span className={styles.mono}>{slot.code}</span>
        <ShelfStatusBadge group={slot.group} status={slot.effective_status} />
        <IconButton
          icon="x"
          label="Закрыть панель"
          variant="ghost"
          size="sm"
          onClick={onClose}
        />
      </div>
      <h2 id="shelf-panel-title" className={styles.panelTitle}>
        {slot.title}
      </h2>
      <Text as="p" tone="muted">
        {subline}
      </Text>

      {mode.kind === "exclude" ? (
        <ShelfExclusionForm
          codes={[slot.code]}
          hasLinkedDocuments={slot.editions.length > 0}
          defaultReason={
            slot.effective_status === "to_clarify"
              ? "condition_not_met"
              : "not_applicable"
          }
          submitting={exclude.isPending}
          serverError={error}
          onCancel={() => {
            setError(null);
            setMode({ kind: "view" });
          }}
          onSubmit={(input) =>
            void run(async () => {
              await exclude.mutateAsync({
                slotId: slot.id,
                version: slot.version,
                ...input,
              });
              setMode({ kind: "view" });
              onExcluded([slot.code], [slot.id]);
            })
          }
        />
      ) : null}

      {mode.kind === "develop" ? (
        <ShelfDevelopForm
          proposedType={slot.proposed_document_type}
          submitting={develop.isPending}
          error={error}
          onCancel={() => setMode({ kind: "view" })}
          onSubmit={(code) => void startDevelop(mode.then, code)}
        />
      ) : null}

      {mode.kind === "link" ? (
        <ShelfLinkPicker
          submitting={link.isPending}
          error={error}
          onCancel={() => setMode({ kind: "view" })}
          onPick={(documentId) =>
            void run(async () => {
              await link.mutateAsync({
                slotId: slot.id,
                documentId,
                version: slot.version,
              });
              setMode({ kind: "view" });
            })
          }
        />
      ) : null}

      {mode.kind === "view" ? (
        <>
          {current && (current.signed_scan || current.working_file) ? (
            <ShelfScanBlock document={current} />
          ) : null}

          {slot.exclusion ? (
            <section
              className={styles.panelBlock}
              aria-label="Исключено с полки"
            >
              <h3 className={styles.panelHeading}>Исключено с полки</h3>
              <dl className={styles.details}>
                <dt>Причина</dt>
                <dd>
                  {EXCLUSION_REASON_LABELS[slot.exclusion.reason] ??
                    slot.exclusion.reason}
                </dd>
                <dt>Комментарий</dt>
                <dd>{slot.exclusion.comment}</dd>
                <dt>Кто и когда</dt>
                <dd>
                  {slot.exclusion.excluded_by_name || "—"} ·{" "}
                  {formatDateTime(slot.exclusion.excluded_at)}
                </dd>
              </dl>
            </section>
          ) : !current && EMPTY_STATES[slot.effective_status] ? (
            <Text as="p" className={styles.emptyNote}>
              {EMPTY_STATES[slot.effective_status]}
            </Text>
          ) : null}

          {error ? (
            <Alert tone="danger" title="Действие не выполнено">
              {error}
            </Alert>
          ) : null}

          {slot.primary_action || others.length > 0 ? (
            <div className={styles.controls} aria-label="Действия">
              {slot.primary_action
                ? renderAction(slot.primary_action, true)
                : null}
              {others.map((action) => renderAction(action, false))}
            </div>
          ) : null}

          <dl className={styles.details}>
            <dt>Основание</dt>
            <dd>
              {slot.legal_basis.source_url ? (
                <a
                  href={slot.legal_basis.source_url}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {slot.legal_basis.regulation || slot.legal_basis.source_url}
                </a>
              ) : (
                slot.legal_basis.regulation || "—"
              )}
            </dd>
            <dt>Пункт</dt>
            <dd>{slot.legal_basis.clause || "—"}</dd>
            {slot.applicability_condition ? (
              <>
                <dt>Условие</dt>
                <dd>{slot.applicability_condition}</dd>
              </>
            ) : null}
            <dt>Пересмотр</dt>
            <dd>
              {slot.review_cycle_text || "—"}
              {slot.review_date
                ? ` · до ${formatDateOnly(slot.review_date)}`
                : ""}
            </dd>
            {current ? (
              <>
                <dt>Редакция</dt>
                <dd>
                  {current.code} ·{" "}
                  {DOCUMENT_STATUS_LABELS[current.status] ?? current.status}
                  {current.effective_from
                    ? ` · с ${formatDateOnly(current.effective_from)}`
                    : ""}
                </dd>
                <dt>Приказ об утверждении</dt>
                <dd>
                  {current.approved_by_order
                    ? `${current.approved_by_order.code} · ${current.approved_by_order.title}`
                    : "—"}
                </dd>
              </>
            ) : null}
          </dl>

          {slot.editions.length > 0 ? (
            <section className={styles.panelBlock} aria-label="Редакции">
              <h3 className={styles.panelHeading}>Редакции</h3>
              <ul className={styles.pickList}>
                {slot.editions.map((edition) => (
                  <li key={edition.id}>
                    <Link href={`/compliance-documents/${edition.id}`}>
                      {edition.code}
                    </Link>{" "}
                    · {DOCUMENT_STATUS_LABELS[edition.status] ?? edition.status}
                    {edition.effective_from
                      ? ` · с ${formatDateOnly(edition.effective_from)}`
                      : ""}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      ) : null}

      {mode.kind === "upload" && uploadDocument.isError ? (
        <Alert tone="danger" title="Не удалось открыть загрузку">
          {shelfErrorMessage(uploadDocument.error)}{" "}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => void uploadDocument.refetch()}
          >
            Повторить
          </Button>{" "}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMode({ kind: "view" })}
          >
            Назад
          </Button>
        </Alert>
      ) : null}
      {mode.kind === "upload" &&
      !uploadDocument.isError &&
      (uploadDocument.isFetching || !uploadDocument.data) ? (
        <Skeleton height="120px" aria-label="Подготовка загрузки" />
      ) : null}
      {/* Opened only with a fresh version: confirm sends it as expected_version. */}
      {mode.kind === "upload" &&
      uploadDocument.data &&
      !uploadDocument.isFetching ? (
        <ComplianceDocumentUploadDialog
          open
          document={uploadDocument.data}
          target={mode.target}
          onUploaded={() => void refreshShelf()}
          onOpenChange={(open) => {
            if (!open) setMode({ kind: "view" });
          }}
        />
      ) : null}
    </aside>
  );
}

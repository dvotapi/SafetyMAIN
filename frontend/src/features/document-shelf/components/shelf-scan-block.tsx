"use client";

import { useState } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogHeader,
  PdfViewer,
  Text,
} from "@/components";

import { getFileDownloadUrl } from "@/features/document-shelf/api/shelf-api";
import { useShelfFileViewUrlQuery } from "@/features/document-shelf/api/shelf-queries";
import styles from "@/features/document-shelf/components/document-shelf.module.css";
import type { ShelfSlotDetailDto } from "@/features/document-shelf/types/shelf-dto";
import { toUserSafeMessage } from "@/services/api/errors";

type CurrentDocument = NonNullable<ShelfSlotDetailDto["current_document"]>;

/** Signed scan first; otherwise the working file, labelled as unsigned (§4.3.6). */
export function ShelfScanBlock({ document }: { document: CurrentDocument }) {
  const file = document.signed_scan ?? document.working_file;
  const kind = document.signed_scan ? "signed_scan" : "working";
  const viewUrl = useShelfFileViewUrlQuery(document.id, file?.file_id ?? null);
  const [fullScreen, setFullScreen] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  if (!file) return null;
  const label = document.signed_scan
    ? "Скан подписанной редакции"
    : "Рабочий файл (без подписи)";
  const title = `${document.code} — ${label}`;

  async function download() {
    setDownloadError(null);
    try {
      const target = await getFileDownloadUrl(document.id, kind);
      window.location.assign(target.url);
    } catch (cause) {
      setDownloadError(toUserSafeMessage(cause));
    }
  }

  return (
    <section className={styles.panelBlock} aria-label={label}>
      <Text as="span" variant="caption" tone="muted">
        {label}
      </Text>
      {viewUrl.isError ? (
        <Alert tone="danger" title="Не удалось открыть файл">
          {toUserSafeMessage(viewUrl.error)}
        </Alert>
      ) : (
        <PdfViewer
          url={viewUrl.data?.url ?? null}
          contentType={file.content_type}
          title={title}
          onDownload={() => void download()}
        />
      )}
      <div className={styles.controls}>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setFullScreen(true)}
        >
          Открыть на весь экран
        </Button>
        <Button variant="secondary" size="sm" onClick={() => void download()}>
          Скачать
        </Button>
      </div>
      {downloadError ? (
        <Alert tone="danger" title="Не удалось скачать">
          {downloadError}
        </Alert>
      ) : null}
      <Dialog open={fullScreen} onOpenChange={setFullScreen}>
        <DialogContent className={styles.fullScreenDialog}>
          <DialogHeader title={title} />
          <DialogBody>
            <PdfViewer
              url={viewUrl.data?.url ?? null}
              contentType={file.content_type}
              title={title}
              onDownload={() => void download()}
              full
            />
          </DialogBody>
        </DialogContent>
      </Dialog>
    </section>
  );
}

"use client";

/**
 * In-browser viewer for PDF and image files (TASK-P11-012 §4.2).
 *
 * pdf.js is loaded lazily when a PDF is shown. The whole file is fetched with
 * one plain GET (`disableRange`, `disableStream`), so the bucket CORS rule for
 * `GET` is enough (ADR-0006 amendment). Other types get only «Скачать».
 */
import clsx from "clsx";
import { useCallback, useEffect, useRef, useState } from "react";

import styles from "@/components/document-viewer/PdfViewer.module.css";
import { Alert, Button, Spinner } from "@/components/primitives";

const IMAGE_TYPES = new Set(["image/png", "image/jpeg"]);
const ZOOM_STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2] as const;
const THUMB_WIDTH = 56;
const MAX_THUMBS = 50;

interface PdfPageProxy {
  getViewport(options: { scale: number }): { width: number; height: number };
  render(options: {
    canvasContext: CanvasRenderingContext2D;
    viewport: { width: number; height: number };
  }): { promise: Promise<unknown> };
}

interface PdfDocumentProxy {
  numPages: number;
  getPage(pageNumber: number): Promise<PdfPageProxy>;
  destroy(): Promise<unknown> | void;
}

async function loadPdf(url: string): Promise<PdfDocumentProxy> {
  const pdfjs = await import("pdfjs-dist");
  if (!pdfjs.GlobalWorkerOptions.workerSrc) {
    pdfjs.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url,
    ).toString();
  }
  const task = pdfjs.getDocument({
    url,
    disableRange: true,
    disableStream: true,
  });
  return (await task.promise) as unknown as PdfDocumentProxy;
}

async function renderPage(
  pdf: PdfDocumentProxy,
  pageNumber: number,
  canvas: HTMLCanvasElement,
  scaleFor: (page: PdfPageProxy) => number,
): Promise<void> {
  const page = await pdf.getPage(pageNumber);
  const viewport = page.getViewport({ scale: scaleFor(page) });
  const context = canvas.getContext("2d");
  if (!context) return;
  canvas.width = Math.floor(viewport.width);
  canvas.height = Math.floor(viewport.height);
  await page.render({ canvasContext: context, viewport }).promise;
}

export interface PdfViewerProps {
  /** Inline (presigned) URL of the file; `null` while it is being issued. */
  url: string | null;
  contentType: string;
  title: string;
  onDownload?: () => void;
  /** Larger layout for the full-screen dialog. */
  full?: boolean;
}

export function PdfViewer({
  url,
  contentType,
  title,
  onDownload,
  full = false,
}: PdfViewerProps) {
  const isPdf = contentType === "application/pdf";
  const isImage = IMAGE_TYPES.has(contentType);
  const [pdf, setPdf] = useState<PdfDocumentProxy | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [zoomIndex, setZoomIndex] = useState(2);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const thumbRefs = useRef<Array<HTMLCanvasElement | null>>([]);

  useEffect(() => {
    if (!isPdf || !url) return undefined;
    let cancelled = false;
    let loaded: PdfDocumentProxy | null = null;
    setPdf(null);
    setError(null);
    setPage(1);
    loadPdf(url)
      .then((document) => {
        loaded = document;
        if (cancelled) void document.destroy();
        else setPdf(document);
      })
      .catch(() => {
        if (!cancelled) setError("Не удалось открыть PDF.");
      });
    return () => {
      cancelled = true;
      if (loaded) void loaded.destroy();
    };
  }, [isPdf, url]);

  const zoom = ZOOM_STEPS[zoomIndex] ?? 1;

  useEffect(() => {
    if (!pdf || !canvasRef.current) return;
    renderPage(
      pdf,
      page,
      canvasRef.current,
      () => zoom * (full ? 1.5 : 1),
    ).catch(() => setError("Не удалось показать страницу."));
  }, [pdf, page, zoom, full]);

  useEffect(() => {
    if (!pdf) return;
    const count = Math.min(pdf.numPages, MAX_THUMBS);
    for (let index = 0; index < count; index += 1) {
      const canvas = thumbRefs.current[index];
      if (!canvas) continue;
      void renderPage(pdf, index + 1, canvas, (proxy) => {
        const base = proxy.getViewport({ scale: 1 });
        return THUMB_WIDTH / base.width;
      }).catch(() => undefined);
    }
  }, [pdf]);

  const pages = pdf?.numPages ?? 0;
  const go = useCallback(
    (next: number) =>
      setPage((current) => Math.min(Math.max(1, next), pages || current)),
    [pages],
  );
  const regionRef = useRef<HTMLDivElement>(null);

  // Keyboard paging while the viewer has focus: arrows, PageUp/PageDown, Home/End.
  useEffect(() => {
    const region = regionRef.current;
    if (!region) return undefined;
    function onKeyDown(event: KeyboardEvent) {
      const moves: Record<string, () => void> = {
        ArrowRight: () => go(page + 1),
        PageDown: () => go(page + 1),
        ArrowLeft: () => go(page - 1),
        PageUp: () => go(page - 1),
        Home: () => go(1),
        End: () => go(pages),
      };
      const move = moves[event.key];
      if (!move || event.target !== region) return;
      event.preventDefault();
      move();
    }
    region.addEventListener("keydown", onKeyDown);
    return () => region.removeEventListener("keydown", onKeyDown);
  }, [go, page, pages]);

  if (!isPdf && !isImage) {
    return (
      <div className={styles.viewer}>
        <Alert tone="info" title="Просмотр недоступен">
          Этот тип файла нельзя показать в браузере.
        </Alert>
        {onDownload ? (
          <Button variant="secondary" onClick={onDownload}>
            Скачать
          </Button>
        ) : null}
      </div>
    );
  }

  if (!url) {
    return (
      <div className={styles.viewer} aria-busy="true">
        <Spinner />
      </div>
    );
  }

  if (isImage) {
    return (
      <div className={clsx(styles.viewer, full && styles.full)}>
        <div className={styles.page}>
          {/* eslint-disable-next-line @next/next/no-img-element -- presigned URL, not optimisable */}
          <img className={styles.image} src={url} alt={title} />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(styles.viewer, full && styles.full)}
      ref={regionRef}
      role="region"
      aria-label={`Просмотр: ${title}`}
      // A scrollable viewer must be focusable for keyboard paging and scrolling.
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
      tabIndex={0}
    >
      <div className={styles.toolbar}>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Предыдущая страница"
          disabled={page <= 1}
          onClick={() => go(page - 1)}
        >
          ‹
        </Button>
        <span aria-live="polite">
          {pages ? `Страница ${page} из ${pages}` : "Загрузка…"}
        </span>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Следующая страница"
          disabled={!pages || page >= pages}
          onClick={() => go(page + 1)}
        >
          ›
        </Button>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Уменьшить"
          disabled={zoomIndex <= 0}
          onClick={() => setZoomIndex((index) => Math.max(0, index - 1))}
        >
          −
        </Button>
        <span>{Math.round(zoom * 100)}%</span>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Увеличить"
          disabled={zoomIndex >= ZOOM_STEPS.length - 1}
          onClick={() =>
            setZoomIndex((index) => Math.min(ZOOM_STEPS.length - 1, index + 1))
          }
        >
          +
        </Button>
      </div>
      {error ? (
        <Alert tone="danger" title="Ошибка просмотра">
          {error}
        </Alert>
      ) : null}
      <div className={styles.body}>
        <ol className={styles.thumbs} aria-label="Страницы">
          {Array.from({ length: Math.min(pages, MAX_THUMBS) }, (_, index) => (
            <li key={index}>
              <button
                type="button"
                className={styles.thumb}
                aria-label={`Страница ${index + 1}`}
                aria-current={index + 1 === page ? "page" : undefined}
                onClick={() => setPage(index + 1)}
              >
                <canvas
                  ref={(element) => {
                    thumbRefs.current[index] = element;
                  }}
                  aria-hidden="true"
                />
              </button>
            </li>
          ))}
        </ol>
        <div className={styles.page}>
          {pdf ? (
            <canvas
              ref={canvasRef}
              aria-label={`${title}, страница ${page}`}
              role="img"
            />
          ) : (
            <Spinner />
          )}
        </div>
      </div>
    </div>
  );
}

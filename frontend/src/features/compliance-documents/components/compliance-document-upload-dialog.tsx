"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  Alert,
  Button,
  Dialog,
  DialogBody,
  DialogContent,
  DialogFooter,
  DialogHeader,
  Label,
  ProgressBar,
  Text,
  useToast,
} from "@/components";

import {
  useConfirmComplianceDocumentFileMutation,
  useCreateComplianceDocumentUploadUrlMutation,
} from "@/features/compliance-documents/api/compliance-documents-mutations";
import type {
  ComplianceDocumentDto,
  ComplianceDocumentUploadUrlDto,
} from "@/features/compliance-documents/types/compliance-documents-dto";
import { toUserSafeMessage } from "@/services/api/errors";

export const ALLOWED_UPLOAD_MIME_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "image/png",
  "image/jpeg",
] as const;

export type AllowedUploadMimeType = (typeof ALLOWED_UPLOAD_MIME_TYPES)[number];

export const DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

const ACCEPT = ALLOWED_UPLOAD_MIME_TYPES.join(",");

export async function computeSha256(file: Blob): Promise<string> {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  const bytes = new Uint8Array(digest);
  let out = "";
  for (let i = 0; i < bytes.length; i += 1) {
    out += bytes[i]!.toString(16).padStart(2, "0");
  }
  return out;
}

function isAllowedType(type: string): type is AllowedUploadMimeType {
  return (ALLOWED_UPLOAD_MIME_TYPES as readonly string[]).includes(type);
}

type Phase = "idle" | "hashing" | "requesting" | "uploading" | "confirming";

function putWithProgress(
  presigned: ComplianceDocumentUploadUrlDto,
  file: File,
  onProgress: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(presigned.method, presigned.url, true);
    for (const [key, value] of Object.entries(presigned.headers)) {
      xhr.setRequestHeader(key, value);
    }
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Загрузка не удалась (HTTP ${xhr.status}).`));
      }
    };
    xhr.onerror = () => reject(new Error("Сетевая ошибка при загрузке файла."));
    xhr.onabort = () => reject(new Error("Загрузка отменена."));
    xhr.send(file);
  });
}

export function ComplianceDocumentUploadDialog({
  open,
  onOpenChange,
  document,
  maxBytes = DEFAULT_MAX_UPLOAD_BYTES,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  document: ComplianceDocumentDto;
  maxBytes?: number;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const uploadUrlMutation = useCreateComplianceDocumentUploadUrlMutation(
    document.id,
  );
  const confirmMutation = useConfirmComplianceDocumentFileMutation(document.id);

  const reset = useCallback(() => {
    setFile(null);
    setPhase("idle");
    setProgress(0);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  useEffect(() => {
    if (open) reset();
  }, [open, reset]);

  const busy = phase !== "idle";

  function pickFile(next: File | null) {
    setError(null);
    if (!next) {
      setFile(null);
      return;
    }
    if (!isAllowedType(next.type)) {
      setError("Недопустимый тип файла. Разрешены PDF, DOCX, XLSX, PNG, JPEG.");
      setFile(null);
      return;
    }
    if (next.size <= 0) {
      setError("Пустые файлы не поддерживаются.");
      setFile(null);
      return;
    }
    if (next.size > maxBytes) {
      setError(
        `Файл слишком большой. Максимум ${(maxBytes / (1024 * 1024)).toFixed(0)} МБ.`,
      );
      setFile(null);
      return;
    }
    setFile(next);
  }

  async function upload() {
    if (!file) return;
    setError(null);
    setProgress(0);
    try {
      setPhase("hashing");
      const sha256 = await computeSha256(file);
      setPhase("requesting");
      const presigned = await uploadUrlMutation.mutateAsync({
        filename: file.name,
        content_type: file.type,
        size_bytes: file.size,
        sha256,
      });
      setPhase("uploading");
      await putWithProgress(presigned, file, setProgress);
      setPhase("confirming");
      await confirmMutation.mutateAsync({
        expected_version: document.version,
        key: presigned.key,
        size_bytes: file.size,
        sha256,
        content_type: file.type,
        original_filename: file.name,
      });
      toast({
        tone: "success",
        title: "Файл загружен",
        description: file.name,
      });
      onOpenChange(false);
    } catch (cause) {
      setError(toUserSafeMessage(cause));
      setPhase("idle");
    }
  }

  const phaseLabel: Record<Phase, string> = {
    idle: "",
    hashing: "Подсчёт SHA-256…",
    requesting: "Получение ссылки на загрузку…",
    uploading: "Загрузка файла…",
    confirming: "Подтверждение…",
  };

  return (
    <Dialog open={open} onOpenChange={busy ? () => undefined : onOpenChange}>
      <DialogContent>
        <DialogHeader
          title="Загрузить файл"
          description={`Документ ${document.code}. Разрешены PDF, DOCX, XLSX, PNG, JPEG.`}
        />
        <DialogBody>
          <div style={{ display: "grid", gap: "var(--sm-space-3)" }}>
            <Label htmlFor="compliance-document-upload-input">Файл</Label>
            <input
              id="compliance-document-upload-input"
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              disabled={busy}
              onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
              data-testid="compliance-document-upload-input"
            />
            {file ? (
              <Text tone="muted" variant="caption">
                {file.name} · {(file.size / 1024).toFixed(1)} КБ
              </Text>
            ) : null}
            {busy ? (
              <div style={{ display: "grid", gap: "var(--sm-space-2)" }}>
                <Text variant="caption">{phaseLabel[phase]}</Text>
                <ProgressBar value={progress} max={100} />
              </div>
            ) : null}
            {error ? (
              <Alert tone="danger" title="Не удалось загрузить файл">
                {error}
              </Alert>
            ) : null}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() => onOpenChange(false)}
          >
            Отмена
          </Button>
          <Button
            variant="primary"
            disabled={!file || busy}
            loading={busy}
            onClick={() => void upload()}
          >
            Загрузить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

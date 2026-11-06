/** Labels of backend-provided actions (display only; the API decides which apply). */
import type { ShelfAction } from "@/features/document-shelf/types/shelf-dto";

export const ACTION_LABELS: Record<ShelfAction, string> = {
  develop_document: "Разработать",
  link_document: "Привязать документ",
  exclude: "Исключить с полки",
  restore: "Вернуть на полку",
  confirm_applicable: "Применимо — нужен документ",
  open_project: "Открыть проект",
  open_document: "Открыть документ",
  upload_scan: "Загрузить скан",
  upload_signed_scan: "Загрузить подписанный скан",
  start_review: "Начать пересмотр",
  send_for_acknowledgement: "Отправить на ознакомление",
};

export const EXCLUSION_REASONS = [
  { value: "not_applicable", label: "Не применимо к организации" },
  { value: "condition_not_met", label: "Условие применимости не выполняется" },
  { value: "duplicate", label: "Дублирует другое место" },
  { value: "other", label: "Другое" },
] as const;

export const EXCLUSION_REASON_LABELS: Record<string, string> =
  Object.fromEntries(EXCLUSION_REASONS.map((item) => [item.value, item.label]));

export const EXCLUSION_COMMENT_MIN_LENGTH = 5;
export const EXCLUSION_COMMENT_MAX_LENGTH = 1000;

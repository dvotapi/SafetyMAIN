/** Russian labels for shelf DTO values (display only, no logic). */
import type {
  ShelfEffectiveStatus,
  ShelfStatusGroup,
} from "@/features/document-shelf/types/shelf-dto";

export const GROUP_LABELS: Record<ShelfStatusGroup, string> = {
  present: "Есть",
  review: "Пересмотр",
  in_progress: "В работе",
  missing: "Нет",
  to_clarify: "Уточнить",
  excluded: "Исключено",
};

export const STATUS_LABELS: Record<ShelfEffectiveStatus, string> = {
  present: "Есть",
  present_unverified: "Есть, документа в системе нет",
  review_due: "Нужен пересмотр",
  overdue_review: "Пересмотр просрочен",
  under_review: "На пересмотре",
  in_progress: "В работе",
  missing: "Нет",
  to_clarify: "Уточнить",
  excluded: "Исключено",
};

export const OBLIGATION_LABELS: Record<string, string> = {
  mandatory: "обязателен",
  conditional: "при условии",
  recommended: "рекомендуется",
};

/** Summary order of TASK §4.3.2 (Готовность is shown separately). */
export const SUMMARY_GROUPS: readonly ShelfStatusGroup[] = [
  "present",
  "in_progress",
  "review",
  "missing",
  "to_clarify",
];

export function pluralPlaces(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "место";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "места";
  return "мест";
}

export function pluralSections(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "разделе";
  return "разделах";
}

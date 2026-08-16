/** Domain-neutral visual statuses (features map backend enums → these). */
export type VisualStatus =
  | "draft"
  | "under_review"
  | "approved"
  | "rejected"
  | "planned"
  | "active"
  | "implemented"
  | "verified_effective"
  | "verified_partially_effective"
  | "verified_ineffective"
  | "overdue"
  | "superseded"
  | "archived"
  | "cancelled"
  | "suspended"
  | "in_implementation";

export type StatusTone =
  "neutral" | "info" | "success" | "warning" | "critical";

export const visualStatusLabels: Record<VisualStatus, string> = {
  draft: "Черновик",
  under_review: "На рассмотрении",
  approved: "Утверждено",
  rejected: "Отклонено",
  planned: "Запланировано",
  active: "Действует",
  implemented: "Внедрено",
  verified_effective: "Подтверждена эффективной",
  verified_partially_effective: "Подтверждена частично эффективной",
  verified_ineffective: "Подтверждена неэффективной",
  overdue: "Просрочено",
  superseded: "Замещено",
  archived: "Архив",
  cancelled: "Отменено",
  suspended: "Приостановлено",
  in_implementation: "Внедряется",
};

export const visualStatusTone: Record<VisualStatus, StatusTone> = {
  draft: "neutral",
  under_review: "info",
  approved: "success",
  rejected: "critical",
  planned: "info",
  active: "success",
  implemented: "neutral",
  verified_effective: "success",
  verified_partially_effective: "warning",
  verified_ineffective: "critical",
  overdue: "warning",
  superseded: "neutral",
  archived: "neutral",
  cancelled: "neutral",
  suspended: "warning",
  in_implementation: "info",
};

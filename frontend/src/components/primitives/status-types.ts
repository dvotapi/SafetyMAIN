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
  draft: "Draft",
  under_review: "Under Review",
  approved: "Approved",
  rejected: "Rejected",
  planned: "Planned",
  active: "Active",
  implemented: "Implemented",
  verified_effective: "Verified Effective",
  verified_partially_effective: "Verified Partially Effective",
  verified_ineffective: "Verified Ineffective",
  overdue: "Overdue",
  superseded: "Superseded",
  archived: "Archived",
  cancelled: "Cancelled",
  suspended: "Suspended",
  in_implementation: "In Implementation",
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

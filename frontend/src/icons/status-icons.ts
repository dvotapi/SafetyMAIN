import type { IconName } from "@/icons";
import type { VisualStatus } from "@/components/primitives/status-types";

export const statusIcons: Record<VisualStatus, IconName> = {
  draft: "file-pen",
  under_review: "eye",
  approved: "badge-check",
  rejected: "badge-x",
  planned: "calendar-clock",
  active: "circle-check",
  implemented: "package-check",
  verified_effective: "shield-check",
  verified_partially_effective: "shield-alert",
  verified_ineffective: "shield-x",
  overdue: "clock-alert",
  superseded: "replace",
  archived: "archive",
  cancelled: "ban",
  suspended: "pause",
  in_implementation: "loader",
};

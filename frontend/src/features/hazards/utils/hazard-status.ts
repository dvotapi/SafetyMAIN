import type { VisualStatus } from "@/components";

import type { HazardStatusDto } from "@/features/hazards/types/hazard-types";

const STATUS_TO_VISUAL: Record<HazardStatusDto, VisualStatus> = {
  draft: "draft",
  active: "active",
  archived: "archived",
};

const STATUS_LABELS: Record<HazardStatusDto, string> = {
  draft: "Draft",
  active: "Active",
  archived: "Archived",
};

export function hazardStatusToVisual(status: HazardStatusDto): VisualStatus {
  return STATUS_TO_VISUAL[status];
}

export function hazardStatusLabel(status: HazardStatusDto): string {
  return STATUS_LABELS[status];
}

export function formatHazardEnumLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

import {
  Archive,
  BadgeCheck,
  BadgeX,
  Ban,
  CalendarClock,
  CircleCheck,
  ClockAlert,
  Eye,
  FilePen,
  Loader,
  PackageCheck,
  Pause,
  Replace,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  type LucideIcon,
} from "lucide-react";

/** Lucide-based icon system (outline, consistent stroke). */
export const icons = {
  archive: Archive,
  "badge-check": BadgeCheck,
  "badge-x": BadgeX,
  ban: Ban,
  "calendar-clock": CalendarClock,
  "circle-check": CircleCheck,
  "clock-alert": ClockAlert,
  "file-pen": FilePen,
  eye: Eye,
  loader: Loader,
  "package-check": PackageCheck,
  pause: Pause,
  replace: Replace,
  "shield-alert": ShieldAlert,
  "shield-check": ShieldCheck,
  "shield-x": ShieldX,
} as const;

export type IconName = keyof typeof icons;

export function getIcon(name: IconName): LucideIcon {
  return icons[name];
}

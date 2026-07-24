export type NavSectionId =
  | "overview"
  | "safety"
  | "people"
  | "knowledge"
  | "analytics"
  | "administration";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  /** Placeholder until permission integration (TASK-P9-004). */
  requiredPermission?: string;
  children?: NavItem[];
}

export interface NavSection {
  id: NavSectionId;
  label: string;
  href: string;
  icon: string;
  children?: NavItem[];
}

/** Typed primary navigation — rendering is separate from structure. */
export const primaryNavigation: NavSection[] = [
  {
    id: "overview",
    label: "Overview",
    href: "/",
    icon: "layout-dashboard",
  },
  {
    id: "safety",
    label: "Safety",
    href: "/safety",
    icon: "shield-check",
    children: [
      { id: "hazards", label: "Hazards", href: "/safety/hazards" },
      {
        id: "risk-assessments",
        label: "Risk Assessments",
        href: "/safety/risk-assessments",
      },
      {
        id: "risk-controls",
        label: "Risk Controls",
        href: "/safety/risk-controls",
      },
    ],
  },
  {
    id: "people",
    label: "People",
    href: "/people",
    icon: "users",
  },
  {
    id: "knowledge",
    label: "Knowledge",
    href: "/knowledge",
    icon: "book-open",
  },
  {
    id: "analytics",
    label: "Analytics",
    href: "/analytics",
    icon: "chart-column",
  },
  {
    id: "administration",
    label: "Administration",
    href: "/administration",
    icon: "settings",
  },
];

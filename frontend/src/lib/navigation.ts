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
  requiredPermission?: string;
  children?: NavItem[];
}

export interface NavSection {
  id: NavSectionId;
  label: string;
  href: string;
  icon: string;
  requiredPermission?: string;
  children?: NavItem[];
}

/** Typed primary navigation — filtered at render by permissions. */
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
    requiredPermission: "hazard:read",
    children: [
      {
        id: "hazards",
        label: "Hazards",
        href: "/safety/hazards",
        requiredPermission: "hazard:read",
      },
      {
        id: "risk-assessments",
        label: "Risk Assessments",
        href: "/safety/risk-assessments",
        requiredPermission: "risk:read",
      },
      {
        id: "risk-controls",
        label: "Risk Controls",
        href: "/safety/risk-controls",
        requiredPermission: "risk_control:read",
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
    requiredPermission: "knowledge_object:read",
  },
  {
    id: "analytics",
    label: "Analytics",
    href: "/analytics",
    icon: "chart-column",
    requiredPermission: "audit:read",
  },
  {
    id: "administration",
    label: "Administration",
    href: "/administration",
    icon: "settings",
    requiredPermission: "user:read",
  },
];

export const PUBLIC_ROUTES = [
  "/login",
  "/unauthorized",
  "/forbidden",
  "/session-expired",
] as const;

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

import type { NavItem, NavSection } from "@/lib/navigation";

export function filterNavigationByPermissions(
  sections: NavSection[],
  hasPermission: (permission: string) => boolean,
): NavSection[] {
  const result: NavSection[] = [];
  for (const section of sections) {
    if (
      section.requiredPermission &&
      !hasPermission(section.requiredPermission)
    ) {
      continue;
    }
    const children = section.children
      ?.filter(
        (child) =>
          !child.requiredPermission || hasPermission(child.requiredPermission),
      )
      .map((child) => ({ ...child }) satisfies NavItem);

    const next: NavSection = {
      id: section.id,
      label: section.label,
      href: section.href,
      icon: section.icon,
    };
    if (section.requiredPermission) {
      next.requiredPermission = section.requiredPermission;
    }
    if (children && children.length > 0) {
      next.children = children;
    }
    result.push(next);
  }
  return result;
}

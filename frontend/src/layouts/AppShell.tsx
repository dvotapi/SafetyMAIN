"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useState, type ReactNode } from "react";

import { OrganizationSwitcher, UserMenu } from "@/components/navigation/Menus";
import { Button } from "@/components/primitives/Button";
import { Text } from "@/components/primitives/Text";
import { useAuth } from "@/features/auth/AuthProvider";
import { filterNavigationByPermissions } from "@/lib/filter-navigation";
import { primaryNavigation } from "@/lib/navigation";
import { useTheme } from "@/theme/theme-provider";
import { cx } from "@/utils/cx";

import styles from "./AppShell.module.css";

const THEME_LABELS = {
  system: "Системная",
  light: "Светлая",
  dark: "Тёмная",
} as const;

function NavTree({
  onNavigate,
  sections,
}: {
  onNavigate?: () => void;
  sections: typeof primaryNavigation;
}) {
  const pathname = usePathname();
  return (
    <ul className={styles.navList}>
      {sections.map((section) => {
        const active =
          pathname === section.href ||
          (section.href !== "/" && pathname.startsWith(section.href));
        return (
          <li key={section.id}>
            <Link
              href={section.href}
              className={cx(styles.navLink, active && styles.navLinkActive)}
              aria-current={active ? "page" : undefined}
              {...(onNavigate ? { onClick: onNavigate } : {})}
            >
              {section.label}
            </Link>
            {section.children ? (
              <ul className={styles.childList}>
                {section.children.map((child) => {
                  const childActive = pathname.startsWith(child.href);
                  return (
                    <li key={child.id}>
                      <Link
                        href={child.href}
                        className={cx(
                          styles.navLink,
                          childActive && styles.navLinkActive,
                        )}
                        aria-current={childActive ? "page" : undefined}
                        {...(onNavigate ? { onClick: onNavigate } : {})}
                      >
                        {child.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { mode, setMode, resolved } = useTheme();
  const { session, currentMembership, logout, hasPermission } = useAuth();
  const router = useRouter();
  const [navOpen, setNavOpen] = useState(false);
  const navId = useId();
  const pathname = usePathname();

  const sections = useMemo(
    () => filterNavigationByPermissions(primaryNavigation, hasPermission),
    [hasPermission],
  );

  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  return (
    <div className={styles.shell}>
      <a href="#main-content" className="skip-link">
        Перейти к содержимому
      </a>
      <header className={styles.topBar} role="banner">
        <div className={styles.topMeta}>
          <Button
            className={styles.navMobileToggle}
            variant="secondary"
            size="sm"
            aria-expanded={navOpen}
            aria-controls={navId}
            onClick={() => setNavOpen((v) => !v)}
          >
            Меню
          </Button>
          <Link href="/" className={styles.brand}>
            SafetyMAIN
          </Link>
        </div>
        <div className={styles.topMeta} aria-label="Организация и пользователь">
          <OrganizationSwitcher
            organizationName={
              currentMembership?.organizationName ?? "Нет организации"
            }
          />
          <label>
            <span className="visually-hidden">Тема</span>
            <select
              aria-label="Режим темы"
              value={mode}
              onChange={(e) =>
                setMode(e.target.value as "system" | "light" | "dark")
              }
            >
              <option value="system">Системная</option>
              <option value="light">Светлая</option>
              <option value="dark">Тёмная</option>
            </select>
          </label>
          <Text as="span" tone="muted" variant="caption">
            {THEME_LABELS[resolved]}
          </Text>
          <UserMenu
            name={session?.user.displayName ?? "Пользователь"}
            items={[
              {
                id: "email",
                label: session?.user.email ?? "",
                disabled: true,
              },
              {
                id: "org",
                label: currentMembership
                  ? `${currentMembership.organizationName} (${currentMembership.role})`
                  : "Нет организации",
                disabled: true,
              },
              {
                id: "profile",
                label: "Профиль (скоро)",
                disabled: true,
              },
              {
                id: "logout",
                label: "Выйти",
                destructive: true,
                onSelect: () => {
                  void logout().then(() => router.replace("/login"));
                },
              },
            ]}
          />
        </div>
      </header>
      <div className={styles.body}>
        <nav
          className={cx(styles.nav, styles.navDesktop)}
          aria-label="Основная"
        >
          <NavTree sections={sections} />
        </nav>
        {navOpen ? (
          <div className={styles.navDrawer}>
            <button
              type="button"
              className={styles.drawerBackdrop}
              aria-label="Закрыть навигацию"
              onClick={() => setNavOpen(false)}
            />
            <nav id={navId} className={styles.drawer} aria-label="Основная">
              <NavTree
                sections={sections}
                onNavigate={() => setNavOpen(false)}
              />
            </nav>
          </div>
        ) : null}
        <main id="main-content" className={styles.main} tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}

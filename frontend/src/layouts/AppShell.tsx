"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState, type ReactNode } from "react";

import { Button } from "@/components/primitives/Button";
import { Text } from "@/components/primitives/Text";
import { primaryNavigation } from "@/lib/navigation";
import { useTheme } from "@/theme/theme-provider";
import { cx } from "@/utils/cx";

import styles from "./AppShell.module.css";

function NavTree({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <ul className={styles.navList}>
      {primaryNavigation.map((section) => {
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
  const [navOpen, setNavOpen] = useState(false);
  const navId = useId();
  const pathname = usePathname();

  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  return (
    <div className={styles.shell}>
      <a href="#main-content" className="skip-link">
        Skip to content
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
            Menu
          </Button>
          <Link href="/" className={styles.brand}>
            SafetyMAIN
          </Link>
        </div>
        <div className={styles.topMeta} aria-label="Organization and user">
          <Text as="span" tone="secondary" variant="caption">
            Organization placeholder
          </Text>
          <label>
            <span className="visually-hidden">Theme</span>
            <select
              aria-label="Theme mode"
              value={mode}
              onChange={(e) =>
                setMode(e.target.value as "system" | "light" | "dark")
              }
            >
              <option value="system">System</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
          <Text as="span" tone="muted" variant="caption">
            {resolved}
          </Text>
          <Text as="span" variant="caption">
            User menu
          </Text>
        </div>
      </header>
      <div className={styles.body}>
        <nav className={cx(styles.nav, styles.navDesktop)} aria-label="Primary">
          <NavTree />
        </nav>
        {navOpen ? (
          <div className={styles.navDrawer}>
            <button
              type="button"
              className={styles.drawerBackdrop}
              aria-label="Close navigation"
              onClick={() => setNavOpen(false)}
            />
            <nav id={navId} className={styles.drawer} aria-label="Primary">
              <NavTree onNavigate={() => setNavOpen(false)} />
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

import { type ReactNode } from "react";

import { Link } from "@/components/primitives/Link";
import { Icon } from "@/icons/Icon";
import type { IconName } from "@/icons";
import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export interface NavigationItemProps {
  href?: string;
  active?: boolean;
  icon?: IconName;
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function NavigationItem({
  href,
  active,
  icon,
  children,
  className,
  onClick,
}: NavigationItemProps) {
  const content = (
    <>
      {icon ? <Icon name={icon} size="sm" decorative /> : null}
      <span>{children}</span>
    </>
  );

  const itemClass = cx(
    styles.navItem,
    active && styles.navItemActive,
    className,
  );

  if (href) {
    return (
      <Link
        href={href}
        className={itemClass}
        aria-current={active ? "page" : undefined}
        {...(onClick ? { onClick } : {})}
      >
        {content}
      </Link>
    );
  }

  return (
    <button type="button" className={itemClass} onClick={onClick}>
      {content}
    </button>
  );
}

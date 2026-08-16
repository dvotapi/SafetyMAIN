import { Fragment, type ReactNode } from "react";

import { Link } from "@/components/primitives/Link";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Navigation.module.css";

export interface BreadcrumbItem {
  label: ReactNode;
  href?: string;
}

export function Breadcrumbs({
  items,
  className,
}: {
  items: BreadcrumbItem[];
  className?: string;
}) {
  return (
    <nav
      aria-label="Хлебные крошки"
      className={cx(styles.breadcrumbs, className)}
    >
      <ol
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "var(--sm-space-1)",
          margin: 0,
          padding: 0,
          listStyle: "none",
        }}
      >
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <Fragment key={`${index}-${String(item.label)}`}>
              <li>
                {item.href && !isLast ? (
                  <Link href={item.href} className={styles.breadcrumbLink}>
                    {item.label}
                  </Link>
                ) : (
                  <span
                    className={styles.breadcrumbCurrent}
                    aria-current={isLast ? "page" : undefined}
                  >
                    {item.label}
                  </span>
                )}
              </li>
              {!isLast ? (
                <li aria-hidden>
                  <Icon name="chevron-right" size="xs" decorative />
                </li>
              ) : null}
            </Fragment>
          );
        })}
      </ol>
    </nav>
  );
}

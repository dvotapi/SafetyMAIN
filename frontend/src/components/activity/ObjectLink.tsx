import { Link } from "@/components/primitives/Link";
import { cx } from "@/utils/cx";

import styles from "./Activity.module.css";

export interface ObjectLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

export function ObjectLink({ href, children, className }: ObjectLinkProps) {
  return (
    <Link href={href} className={cx(styles.objectLink, className)}>
      {children}
    </Link>
  );
}

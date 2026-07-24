import NextLink from "next/link";
import { type ComponentProps, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Link.module.css";

export interface LinkProps extends ComponentProps<typeof NextLink> {
  children: ReactNode;
  external?: boolean;
}

export function Link({
  children,
  className,
  external,
  rel,
  target,
  ...rest
}: LinkProps) {
  const isExternal = external ?? String(rest.href).startsWith("http");
  return (
    <NextLink
      className={cx(styles.link, className)}
      rel={isExternal ? (rel ?? "noopener noreferrer") : rel}
      target={isExternal ? (target ?? "_blank") : target}
      {...rest}
    >
      {children}
    </NextLink>
  );
}

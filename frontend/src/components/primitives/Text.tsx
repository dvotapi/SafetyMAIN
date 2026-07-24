import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Text.module.css";

type Tone = "default" | "secondary" | "muted";
type Variant = "body" | "label" | "caption" | "code";

export interface TextProps extends HTMLAttributes<HTMLParagraphElement> {
  tone?: Tone;
  variant?: Variant;
  as?: "p" | "span" | "div";
  children: ReactNode;
}

export function Text({
  tone = "default",
  variant = "body",
  as: Comp = "p",
  className,
  children,
  ...rest
}: TextProps) {
  return (
    <Comp
      className={cx(
        styles.text,
        styles[variant],
        tone === "muted" && styles.muted,
        tone === "secondary" && styles.secondary,
        className,
      )}
      {...rest}
    >
      {children}
    </Comp>
  );
}

export interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  level?: 1 | 2 | 3;
  children: ReactNode;
}

export function Heading({
  level = 1,
  className,
  children,
  ...rest
}: HeadingProps) {
  const Comp = `h${level}` as const;
  const sizeClass =
    level === 1 ? styles.h1 : level === 2 ? styles.h2 : styles.h3;
  return (
    <Comp className={cx(styles.heading, sizeClass, className)} {...rest}>
      {children}
    </Comp>
  );
}

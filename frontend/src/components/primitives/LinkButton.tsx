"use client";

import { type ComponentProps } from "react";

import { Link, type LinkProps } from "@/components/primitives/Link";
import { cx } from "@/utils/cx";

import styles from "./LinkButton.module.css";

export type LinkButtonSize = "sm" | "md";

export interface LinkButtonProps extends LinkProps {
  size?: LinkButtonSize;
}

export function LinkButton({
  size = "md",
  className,
  ...rest
}: LinkButtonProps) {
  return (
    <Link
      className={cx(styles.linkButton, styles[size], className)}
      {...rest}
    />
  );
}

export interface NativeLinkButtonProps extends ComponentProps<"button"> {
  size?: LinkButtonSize;
}

export function NativeLinkButton({
  size = "md",
  className,
  type = "button",
  ...rest
}: NativeLinkButtonProps) {
  return (
    <button
      type={type}
      className={cx(styles.linkButton, styles[size], className)}
      {...rest}
    />
  );
}

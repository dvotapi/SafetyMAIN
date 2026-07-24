"use client";

import { type LucideProps } from "lucide-react";

import { getIcon, type IconName } from "@/icons";
import { cx } from "@/utils/cx";

export type IconSize = "xs" | "sm" | "md" | "lg" | "xl";

const sizeVar: Record<IconSize, string> = {
  xs: "var(--sm-size-icon-xs)",
  sm: "var(--sm-size-icon-sm)",
  md: "var(--sm-size-icon-md)",
  lg: "var(--sm-size-icon-lg)",
  xl: "var(--sm-size-icon-xl)",
};

export interface IconProps extends Omit<LucideProps, "ref" | "size"> {
  name: IconName;
  size?: IconSize;
  /** Decorative icons must set aria-hidden (default true when no title/label). */
  decorative?: boolean;
  title?: string;
}

export function Icon({
  name,
  size = "md",
  decorative,
  title,
  className,
  strokeWidth = 1.75,
  ...rest
}: IconProps) {
  const Cmp = getIcon(name);
  const isDecorative = decorative ?? !title;
  return (
    <Cmp
      className={cx("sm-icon", className)}
      strokeWidth={strokeWidth}
      aria-hidden={isDecorative ? true : undefined}
      role={isDecorative ? undefined : "img"}
      aria-label={!isDecorative ? title : undefined}
      style={{ width: sizeVar[size], height: sizeVar[size] }}
      {...rest}
    />
  );
}

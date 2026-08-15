import { type HTMLAttributes } from "react";

import { cx } from "@/utils/cx";

import styles from "./DataDisplay.module.css";

export type AvatarSize = "sm" | "md" | "lg";

export interface AvatarProps extends HTMLAttributes<HTMLSpanElement> {
  name: string;
  src?: string;
  size?: AvatarSize;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function avatarSizeClass(size: AvatarSize): string {
  if (size === "sm") return styles.avatarSm ?? "";
  if (size === "lg") return styles.avatarLg ?? "";
  return styles.avatarMd ?? "";
}

export function Avatar({
  name,
  src,
  size = "md",
  className,
  ...rest
}: AvatarProps) {
  return (
    <span
      className={cx(styles.avatar, avatarSizeClass(size), className)}
      title={name}
      aria-label={name}
      {...rest}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" className={styles.avatarImage} />
      ) : (
        initials(name)
      )}
    </span>
  );
}

import { forwardRef, type ButtonHTMLAttributes } from "react";

import { Icon, type IconSize } from "@/icons/Icon";
import type { IconName } from "@/icons";
import { cx } from "@/utils/cx";

import styles from "./Button.module.css";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: IconName;
  label: string;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  iconSize?: IconSize;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  function IconButton(
    {
      icon,
      label,
      variant = "ghost",
      size = "md",
      iconSize = "md",
      className,
      type = "button",
      ...rest
    },
    ref,
  ) {
    return (
      <button
        ref={ref}
        type={type}
        aria-label={label}
        className={cx(styles.button, styles[variant], styles[size], className)}
        {...rest}
      >
        <Icon name={icon} size={iconSize} decorative />
      </button>
    );
  },
);

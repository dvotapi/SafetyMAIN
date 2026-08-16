import { Slot } from "@radix-ui/react-slot";
import { type ButtonHTMLAttributes, forwardRef, type ReactNode } from "react";

import { Spinner } from "@/components/feedback/Feedback";
import { cx } from "@/utils/cx";

import styles from "./Button.module.css";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
  loading?: boolean;
  children: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = "primary",
      size = "md",
      asChild = false,
      loading = false,
      className,
      type = "button",
      disabled,
      children,
      ...rest
    },
    ref,
  ) {
    const isDisabled = disabled || loading;
    const classes = cx(
      styles.button,
      styles[variant],
      styles[size],
      loading && styles.loading,
      className,
    );

    if (asChild) {
      return (
        <Slot
          ref={ref}
          className={classes}
          aria-busy={loading || undefined}
          {...rest}
        >
          {children}
        </Slot>
      );
    }

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={loading || undefined}
        className={classes}
        {...rest}
      >
        {loading ? (
          <span className={styles.loadingSpinner} aria-hidden>
            <Spinner className={styles.buttonSpinner} label="Загрузка" />
          </span>
        ) : null}
        <span className={cx(loading && styles.loadingContent)}>{children}</span>
      </button>
    );
  },
);

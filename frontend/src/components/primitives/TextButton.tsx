import { type ButtonHTMLAttributes, forwardRef, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./TextButton.module.css";

export type TextButtonSize = "sm" | "md";
export type TextButtonTone = "default" | "danger";

export interface TextButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: TextButtonSize;
  tone?: TextButtonTone;
  children: ReactNode;
}

export const TextButton = forwardRef<HTMLButtonElement, TextButtonProps>(
  function TextButton(
    { size = "md", tone = "default", className, type = "button", ...rest },
    ref,
  ) {
    return (
      <button
        ref={ref}
        type={type}
        className={cx(
          styles.textButton,
          styles[size],
          tone === "danger" && styles.danger,
          className,
        )}
        {...rest}
      />
    );
  },
);

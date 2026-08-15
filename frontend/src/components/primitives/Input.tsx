import React, {
  forwardRef,
  type InputHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

import { Button } from "@/components/primitives/Button";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Field.module.css";

type ControlSize = "sm" | "md" | "lg";

function sizeClass(size: ControlSize | undefined): string | undefined {
  if (size === "sm") return styles.controlSm;
  if (size === "lg") return styles.controlLg;
  return undefined;
}

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
  inputSize?: ControlSize;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, invalid, inputSize = "md", type = "text", ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      aria-invalid={invalid || undefined}
      className={cx(
        styles.control,
        sizeClass(inputSize),
        invalid && styles.controlError,
        className,
      )}
      {...rest}
    />
  );
});

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  invalid?: boolean;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  function TextArea({ className, invalid, ...rest }, ref) {
    return (
      <textarea
        ref={ref}
        aria-invalid={invalid || undefined}
        className={cx(
          styles.control,
          styles.textarea,
          invalid && styles.controlError,
          className,
        )}
        {...rest}
      />
    );
  },
);

export interface SearchInputProps extends Omit<InputProps, "type"> {
  onClear?: () => void;
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  function SearchInput({ className, onClear, value, ...rest }, ref) {
    const hasValue = String(value ?? "").length > 0;
    return (
      <div className={styles.affix}>
        <Icon name="search" size="sm" decorative className={styles.affixIcon} />
        <Input
          ref={ref}
          type="search"
          value={value}
          className={cx(styles.affixControl, className)}
          {...rest}
        />
        {onClear && hasValue ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={styles.affixEnd}
            aria-label="Clear search"
            onClick={onClear}
          >
            Clear
          </Button>
        ) : null}
      </div>
    );
  },
);

export interface PasswordInputProps extends Omit<InputProps, "type"> {
  revealLabel?: string;
  hideLabel?: string;
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput(
    {
      className,
      revealLabel = "Show password",
      hideLabel = "Hide password",
      autoComplete,
      ...rest
    },
    ref,
  ) {
    const [visible, setVisible] = React.useState(false);
    return (
      <div className={styles.affix}>
        <Input
          ref={ref}
          type={visible ? "text" : "password"}
          className={className}
          autoComplete={autoComplete ?? "current-password"}
          {...rest}
        />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className={styles.affixEnd}
          aria-label={visible ? hideLabel : revealLabel}
          onClick={() => setVisible((v) => !v)}
        >
          {visible ? "Hide" : "Show"}
        </Button>
      </div>
    );
  },
);

export type NumberInputProps = Omit<InputProps, "type">;

export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(
  function NumberInput(props, ref) {
    return <Input ref={ref} type="number" inputMode="decimal" {...props} />;
  },
);

export type DatePickerProps = Omit<InputProps, "type">;
export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  function DatePicker(props, ref) {
    return <Input ref={ref} type="date" {...props} />;
  },
);

export type TimePickerProps = Omit<InputProps, "type">;
export const TimePicker = forwardRef<HTMLInputElement, TimePickerProps>(
  function TimePicker(props, ref) {
    return <Input ref={ref} type="time" {...props} />;
  },
);

export type DateTimePickerProps = Omit<InputProps, "type">;
export const DateTimePicker = forwardRef<HTMLInputElement, DateTimePickerProps>(
  function DateTimePicker(props, ref) {
    return <Input ref={ref} type="datetime-local" {...props} />;
  },
);

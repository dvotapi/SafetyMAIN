"use client";

import * as Popover from "@radix-ui/react-popover";
import * as SelectPrimitive from "@radix-ui/react-select";
import {
  type ComponentPropsWithoutRef,
  type ReactNode,
  useMemo,
  useState,
} from "react";

import { Button } from "@/components/primitives/Button";
import { Checkbox } from "@/components/primitives/Control";
import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Select.module.css";

export interface SelectOption {
  value: string;
  label: ReactNode;
  disabled?: boolean;
}

export interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  options: SelectOption[];
  disabled?: boolean;
  invalid?: boolean;
  name?: string;
  id?: string;
  className?: string;
  triggerClassName?: string;
}

export function Select({
  value,
  defaultValue,
  onValueChange,
  placeholder = "Выберите…",
  options,
  disabled,
  invalid,
  name,
  id,
  className,
  triggerClassName,
}: SelectProps) {
  const selectProps = {
    ...(value !== undefined ? { value } : {}),
    ...(defaultValue !== undefined ? { defaultValue } : {}),
    ...(onValueChange ? { onValueChange } : {}),
    ...(name ? { name } : {}),
    ...(disabled ? { disabled } : {}),
  };

  return (
    <SelectPrimitive.Root {...selectProps}>
      <SelectPrimitive.Trigger
        id={id}
        className={cx(
          styles.trigger,
          invalid && styles.triggerError,
          className,
          triggerClassName,
        )}
        aria-invalid={invalid || undefined}
      >
        <SelectPrimitive.Value placeholder={placeholder} />
        <SelectPrimitive.Icon>
          <Icon name="chevron-down" size="sm" decorative />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          className={styles.content}
          position="popper"
          sideOffset={4}
        >
          <SelectPrimitive.Viewport className={styles.viewport}>
            {options.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                {...(option.disabled ? { disabled: true } : {})}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  );
}

function SelectItem({
  children,
  className,
  ...rest
}: ComponentPropsWithoutRef<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item className={cx(styles.item, className)} {...rest}>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
      <SelectPrimitive.ItemIndicator className={styles.itemIndicator}>
        <Icon name="check" size="sm" decorative />
      </SelectPrimitive.ItemIndicator>
    </SelectPrimitive.Item>
  );
}

export interface MultiSelectProps {
  values?: string[];
  defaultValues?: string[];
  onValuesChange?: (values: string[]) => void;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  id?: string;
  className?: string;
}

export function MultiSelect({
  values,
  defaultValues,
  onValuesChange,
  options,
  placeholder = "Выберите…",
  disabled,
  invalid,
  id,
  className,
}: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [internalValues, setInternalValues] = useState<string[]>(
    defaultValues ?? [],
  );
  const selected = values ?? internalValues;

  const labelByValue = useMemo(
    () => new Map(options.map((option) => [option.value, option.label])),
    [options],
  );

  const displayLabel =
    selected.length === 0
      ? placeholder
      : selected
          .map((value) => labelByValue.get(value))
          .filter(Boolean)
          .join(", ");

  function updateValues(next: string[]) {
    if (values === undefined) {
      setInternalValues(next);
    }
    onValuesChange?.(next);
  }

  function toggleValue(value: string) {
    updateValues(
      selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value],
    );
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          id={id}
          type="button"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          data-invalid={invalid ? "true" : undefined}
          className={cx(
            styles.trigger,
            styles.multiTrigger,
            invalid && styles.triggerError,
            className,
          )}
        >
          <span
            className={cx(
              styles.multiLabel,
              selected.length === 0 && styles.placeholder,
            )}
          >
            {displayLabel}
          </span>
          <Icon name="chevron-down" size="sm" decorative />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content className={cx(styles.content, styles.multiContent)}>
          <div className={styles.multiList}>
            {options.map((option) => (
              <Checkbox
                key={option.value}
                checked={selected.includes(option.value)}
                {...(option.disabled ? { disabled: true } : {})}
                onCheckedChange={() => toggleValue(option.value)}
              >
                {option.label}
              </Checkbox>
            ))}
          </div>
          <div className={styles.multiActions}>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => updateValues([])}
            >
              Очистить
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={() => setOpen(false)}
            >
              Готово
            </Button>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

"use client";

import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import * as SwitchPrimitive from "@radix-ui/react-switch";
import {
  type ComponentPropsWithoutRef,
  type ReactNode,
  forwardRef,
} from "react";

import { Icon } from "@/icons/Icon";
import { cx } from "@/utils/cx";

import styles from "./Control.module.css";

export interface CheckboxProps extends ComponentPropsWithoutRef<
  typeof CheckboxPrimitive.Root
> {
  label?: ReactNode;
}

export const Checkbox = forwardRef<HTMLButtonElement, CheckboxProps>(
  function Checkbox({ className, label, id, children, ...rest }, ref) {
    const content = children ?? label;
    return (
      <label
        className={cx(styles.root, styles.checkbox, className)}
        htmlFor={id}
      >
        <CheckboxPrimitive.Root
          ref={ref}
          id={id}
          className={styles.indicator}
          {...rest}
        >
          <CheckboxPrimitive.Indicator>
            <Icon name="check" size="sm" decorative />
          </CheckboxPrimitive.Indicator>
        </CheckboxPrimitive.Root>
        {content ? <span className={styles.label}>{content}</span> : null}
      </label>
    );
  },
);

export interface RadioProps extends ComponentPropsWithoutRef<
  typeof RadioGroupPrimitive.Item
> {
  label?: ReactNode;
}

export const Radio = forwardRef<HTMLButtonElement, RadioProps>(function Radio(
  { className, label, id, children, ...rest },
  ref,
) {
  const content = children ?? label;
  return (
    <label className={cx(styles.root, styles.radio, className)} htmlFor={id}>
      <RadioGroupPrimitive.Item
        ref={ref}
        id={id}
        className={styles.indicator}
        {...rest}
      >
        <RadioGroupPrimitive.Indicator className={styles.radioDot} />
      </RadioGroupPrimitive.Item>
      {content ? <span className={styles.label}>{content}</span> : null}
    </label>
  );
});

export interface RadioGroupProps extends ComponentPropsWithoutRef<
  typeof RadioGroupPrimitive.Root
> {
  inline?: boolean;
}

export const RadioGroup = forwardRef<HTMLDivElement, RadioGroupProps>(
  function RadioGroup({ className, inline, ...rest }, ref) {
    return (
      <RadioGroupPrimitive.Root
        ref={ref}
        className={cx(
          styles.radioGroup,
          inline && styles.radioGroupInline,
          className,
        )}
        {...rest}
      />
    );
  },
);

export type SwitchProps = ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>;

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(
  function Switch({ className, ...rest }, ref) {
    return (
      <SwitchPrimitive.Root
        ref={ref}
        className={cx(styles.switchRoot, className)}
        {...rest}
      >
        <SwitchPrimitive.Thumb className={styles.switchThumb} />
      </SwitchPrimitive.Root>
    );
  },
);

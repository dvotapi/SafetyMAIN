"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import {
  type ComponentPropsWithoutRef,
  type ReactNode,
  forwardRef,
} from "react";

import { IconButton } from "@/components/primitives/IconButton";
import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Dialog.module.css";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogOverlay({
  className,
  ...rest
}: ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      className={cx(styles.overlay, className)}
      {...rest}
    />
  );
}

export interface DialogContentProps extends ComponentPropsWithoutRef<
  typeof DialogPrimitive.Content
> {
  showClose?: boolean;
}

export const DialogContent = forwardRef<HTMLDivElement, DialogContentProps>(
  function DialogContent(
    { className, children, showClose = true, ...rest },
    ref,
  ) {
    return (
      <DialogPrimitive.Portal>
        <DialogOverlay />
        <DialogPrimitive.Content
          ref={ref}
          className={cx(styles.content, className)}
          {...rest}
        >
          {children}
          {showClose ? (
            <DialogPrimitive.Close asChild>
              <IconButton
                icon="x"
                label="Close dialog"
                variant="ghost"
                size="sm"
                iconSize="sm"
                className={styles.closeButton}
              />
            </DialogPrimitive.Close>
          ) : null}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    );
  },
);

export function DialogHeader({
  title,
  description,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.header, className)}>
      <div>
        <DialogPrimitive.Title asChild>
          <Heading level={2}>{title}</Heading>
        </DialogPrimitive.Title>
        {description ? (
          <DialogPrimitive.Description asChild>
            <Text tone="secondary">{description}</Text>
          </DialogPrimitive.Description>
        ) : null}
      </div>
    </div>
  );
}

export function DialogBody({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx(styles.body, className)}>{children}</div>;
}

export function DialogFooter({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cx(styles.footer, className)}>{children}</div>;
}

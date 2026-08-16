"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { type ReactNode } from "react";

import { IconButton } from "@/components/primitives/IconButton";
import { Heading, Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Dialog.module.css";

export function SideDrawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <DialogPrimitive.Root {...rootProps}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className={styles.drawerOverlay} />
        <DialogPrimitive.Content className={cx(styles.sideDrawer, className)}>
          <div className={styles.drawerHeader}>
            <div className={styles.header}>
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
              <DialogPrimitive.Close asChild>
                <IconButton
                  icon="x"
                  label="Закрыть панель"
                  variant="ghost"
                  size="sm"
                  iconSize="sm"
                />
              </DialogPrimitive.Close>
            </div>
          </div>
          <div className={styles.drawerBody}>{children}</div>
          {footer ? <div className={styles.drawerFooter}>{footer}</div> : null}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export function BottomDrawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  const rootProps = {
    ...(open !== undefined ? { open } : {}),
    ...(onOpenChange ? { onOpenChange } : {}),
  };

  return (
    <DialogPrimitive.Root {...rootProps}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className={styles.drawerOverlay} />
        <DialogPrimitive.Content className={cx(styles.bottomDrawer, className)}>
          <div className={styles.drawerHeader}>
            <div className={styles.header}>
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
              <DialogPrimitive.Close asChild>
                <IconButton
                  icon="x"
                  label="Закрыть панель"
                  variant="ghost"
                  size="sm"
                  iconSize="sm"
                />
              </DialogPrimitive.Close>
            </div>
          </div>
          <div className={styles.drawerBody}>{children}</div>
          {footer ? <div className={styles.drawerFooter}>{footer}</div> : null}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

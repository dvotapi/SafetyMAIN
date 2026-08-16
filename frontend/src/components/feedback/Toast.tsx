"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { IconButton } from "@/components/primitives/IconButton";
import { Text } from "@/components/primitives/Text";
import { cx } from "@/utils/cx";

import styles from "./Feedback.module.css";

export type ToastTone = "info" | "success" | "warning" | "danger";

export interface ToastData {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  tone?: ToastTone;
}

interface ToastContextValue {
  toast: (input: Omit<ToastData, "id">) => string;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

function createToastId() {
  return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const toast = useCallback((input: Omit<ToastData, "id">) => {
    const id = createToastId();
    setToasts((current) => [...current, { ...input, id }]);
    return id;
  }, []);

  const value = useMemo(() => ({ toast, dismiss }), [toast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

export function ToastViewport({
  toasts,
  onDismiss,
}: {
  toasts: ToastData[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div
      className={styles.toastViewport}
      aria-live="polite"
      aria-relevant="additions"
    >
      {toasts.map((item) => (
        <Toast key={item.id} {...item} onDismiss={() => onDismiss(item.id)} />
      ))}
    </div>
  );
}

function Toast({
  title,
  description,
  tone = "info",
  onDismiss,
}: ToastData & { onDismiss: () => void }) {
  return (
    <div
      className={cx(styles.toast, styles[`toast${capitalize(tone)}`])}
      role="status"
    >
      <div className={styles.toastContent}>
        <Text as="div" variant="label">
          {title}
        </Text>
        {description ? (
          <Text as="div" tone="secondary" variant="caption">
            {description}
          </Text>
        ) : null}
      </div>
      <IconButton
        icon="x"
        label="Закрыть уведомление"
        variant="ghost"
        size="sm"
        iconSize="sm"
        onClick={onDismiss}
      />
    </div>
  );
}

function capitalize(value: ToastTone): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

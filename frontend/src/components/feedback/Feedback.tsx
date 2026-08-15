import { type HTMLAttributes, type ReactNode } from "react";

import { cx } from "@/utils/cx";

import styles from "./Feedback.module.css";

export function Spinner({
  className,
  label = "Loading",
  ...rest
}: HTMLAttributes<HTMLDivElement> & { label?: string }) {
  return (
    <div
      className={cx(styles.spinner, className)}
      role="status"
      aria-label={label}
      {...rest}
    />
  );
}

export function Skeleton({
  className,
  width,
  height,
  ...rest
}: HTMLAttributes<HTMLDivElement> & { width?: string; height?: string }) {
  return (
    <div
      className={cx(styles.skeleton, className)}
      style={{ width, height }}
      aria-hidden
      {...rest}
    />
  );
}

export type AlertTone = "info" | "success" | "warning" | "danger";

export function Alert({
  tone = "info",
  title,
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement> & {
  tone?: AlertTone;
  title?: string;
  children: ReactNode;
}) {
  return (
    <div
      role="alert"
      className={cx(styles.alert, styles[tone], className)}
      {...rest}
    >
      <div>
        {title ? <strong>{title}</strong> : null}
        <div>{children}</div>
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.emptyState, className)}>
      <div className={styles.emptyTitle}>{title}</div>
      {description ? (
        <div className={styles.emptyDescription}>{description}</div>
      ) : null}
      {action ? <div className={styles.emptyAction}>{action}</div> : null}
    </div>
  );
}

export function LoadingState({
  label = "Loading",
  description,
  className,
}: {
  label?: string;
  description?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx(styles.loadingState, className)} role="status">
      <Spinner label={label} />
      <div className={styles.loadingLabel}>{label}</div>
      {description ? (
        <div className={styles.loadingDescription}>{description}</div>
      ) : null}
    </div>
  );
}

export function Banner({
  tone = "info",
  title,
  children,
  action,
  className,
}: HTMLAttributes<HTMLDivElement> & {
  tone?: AlertTone;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={cx(styles.banner, styles[`banner${tone}`], className)}>
      <div className={styles.bannerContent}>
        {title ? <div className={styles.bannerTitle}>{title}</div> : null}
        {children}
      </div>
      {action ? <div className={styles.bannerAction}>{action}</div> : null}
    </div>
  );
}

export type { ToastData, ToastTone } from "@/components/feedback/Toast";
export {
  ToastProvider,
  ToastViewport,
  useToast,
} from "@/components/feedback/Toast";

export function NotificationItem({
  title,
  description,
  meta,
  unread,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  meta?: ReactNode;
  unread?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cx(
        styles.notificationItem,
        unread && styles.notificationUnread,
        className,
      )}
    >
      <div className={styles.notificationMain}>
        <div className={styles.notificationTitle}>{title}</div>
        {description ? (
          <div className={styles.notificationDescription}>{description}</div>
        ) : null}
      </div>
      {meta ? <div className={styles.notificationMeta}>{meta}</div> : null}
    </div>
  );
}

export function ProgressBar({
  value,
  max = 100,
  label,
  className,
}: {
  value: number;
  max?: number;
  label?: string;
  className?: string;
}) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div
      className={cx(styles.progressBar, className)}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={label}
    >
      <div className={styles.progressFill} style={{ width: `${percent}%` }} />
    </div>
  );
}

export function ProgressRing({
  value,
  max = 100,
  size = 48,
  label,
  className,
}: {
  value: number;
  max?: number;
  size?: number;
  label?: string;
  className?: string;
}) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));
  const stroke = 4;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div
      className={cx(styles.progressRing, className)}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={label}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          className={styles.progressRingTrack}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
        />
        <circle
          className={styles.progressRingFill}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <span className={styles.progressRingLabel}>{Math.round(percent)}%</span>
    </div>
  );
}
